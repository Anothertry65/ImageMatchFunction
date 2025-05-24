import logging
import azure.functions as func
from PIL import Image
import imagehash
import io
from azure.storage.blob import BlobServiceClient
import cv2
import numpy as np
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", path="low-def-tiffs/{name}", connection="AzureWebJobsStorage")
def TiffUploadTrigger(myblob: func.InputStream):
    logging.info(f"Triggered by blob: {myblob.name}")

    # Storage connection
    conn_str = os.environ["AzureWebJobsStorage"]
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)

    # Extract first page of TIFF
    tiff_stream = io.BytesIO(myblob.read())
    with Image.open(tiff_stream) as tiff_img:
        tiff_img.seek(0)  # First page
        tiff_cv = cv2.cvtColor(np.array(tiff_img), cv2.COLOR_RGB2BGR)
        tiff_hash = imagehash.average_hash(Image.fromarray(tiff_cv))

    # Compare with hi-def-images
    container_client = blob_service_client.get_container_client("hi-def-images")
    blobs = container_client.list_blobs()
    match = None

    for blob in blobs:
        blob_client = container_client.get_blob_client(blob.name)
        jpg_stream = blob_client.download_blob().readall()
        with Image.open(io.BytesIO(jpg_stream)) as jpg_img:
            jpg_cv = cv2.cvtColor(np.array(jpg_img), cv2.COLOR_RGB2BGR)
            jpg_hash = imagehash.average_hash(Image.fromarray(jpg_cv))
            if tiff_hash - jpg_hash < 10:  # Threshold for similarity
                match = blob.name
                break

    # Send email
    if match:
        sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
        message = Mail(
            from_email="no-reply@core2image2blobs.com",
            to_emails="PictureScanner@pwdi.net",
            subject="Image Match Found",
            plain_text_content=f"Matching JPG: {match}")
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
        logging.info(f"Emailed match: {match}")
    else:
        logging.info("No match found.")