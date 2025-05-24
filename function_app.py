###   Pushing to Azure again.....  

import logging
import azure.functions as func
from PIL import Image
import imagehash
import io
from azure.storage.blob import BlobServiceClient
import csv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", path="low-def-tiffs/{name}", connection="AzureWebJobsStorage")
def TiffUploadTrigger(myblob: func.InputStream):
    logging.info(f"Triggered by blob: {myblob.name}")
    try:
        # Storage connection
        logging.info("Fetching connection string")
        conn_str = os.environ["AzureWebJobsStorage"]
        logging.info("Initializing BlobServiceClient")
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)

        # Extract first page of TIFF
        logging.info(f"Reading TIFF stream: {myblob.name}")
        tiff_data = myblob.read()
        logging.info(f"TIFF data read, length: {len(tiff_data)} bytes")
        tiff_stream = io.BytesIO(tiff_data)
        logging.info(f"Opening TIFF: {myblob.name}")
        with Image.open(tiff_stream) as tiff_img:
            logging.info(f"Seeking first page of TIFF: {myblob.name}")
            tiff_img.seek(0)
            logging.info(f"Converting TIFF to greyscale: {myblob.name}")
            tiff_img_grey = tiff_img.convert("L")
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(tiff_img_grey)
            logging.info(f"TIFF hash computed: {tiff_hash}")

        # Compare with hi-def-images
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None
        match_distance = None

        for blob in blobs:
            try:
                logging.info(f"Processing blob: {blob.name}")
                blob_client = container_client.get_blob_client(blob.name)
                logging.info(f"Downloading JPG: {blob.name}")
                jpg_stream = blob_client.download_blob().readall()
                logging.info(f"JPG downloaded, length: {len(jpg_stream)} bytes")
                
                logging.info(f"Opening JPG: {blob.name}")
                with Image.open(io.BytesIO(jpg_stream)) as jpg_img:
                    logging.info(f"Converting JPG to greyscale: {blob.name}")
                    jpg_img_grey = jpg_img.convert("L")
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(jpg_img_grey)
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 15:  # Threshold for similarity
                        match = blob.name
                        match_distance = distance
                        logging.info(f"Match found: {match} with distance {distance}")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue

        # Generate CSV in memory
        logging.info("Generating CSV")
        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output)
        csv_writer.writerow(["TIFF_File", "JPG_File", "Hash_Distance"])  # CSV header
        jpg_filename = match if match else ""
        distance_value = match_distance if match_distance is not None else ""
        csv_writer.writerow([myblob.name, jpg_filename, distance_value])
        csv_content = csv_output.getvalue()
        csv_output.close()
        logging.info(f"CSV content generated: {csv_content}")

        # Upload CSV to output-csvs container
        logging.info("Uploading CSV to output-csvs container")
        output_container = "output-csvs"
        try:
            container_client = blob_service_client.get_container_client(output_container)
            # Create container if it doesn't exist
            try:
                container_client.create_container()
                logging.info(f"Created container: {output_container}")
            except Exception as e:
                if "ContainerAlreadyExists" not in str(e):
                    raise
                logging.info(f"Container {output_container} already exists")

            # Generate unique CSV filename using timestamp and TIFF name
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            tiff_basename = os.path.basename(myblob.name).replace(".tiff", "").replace(".tif", "")
            csv_blob_name = f"matches_{tiff_basename}_{timestamp}.csv"
            blob_client = container_client.get_blob_client(csv_blob_name)
            blob_client.upload_blob(csv_content, overwrite=True)
            logging.info(f"CSV uploaded: {csv_blob_name}")
        except Exception as e:
            logging.error(f"Failed to upload CSV: {str(e)}")
            raise

        # Send email
        logging.info("Preparing to send email")
        try:
            logging.info("Fetching SENDGRID_API_KEY from environment")
            sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
            logging.info("SENDGRID_API_KEY fetched, initializing SendGrid client")
            sg = SendGridAPIClient(sendgrid_api_key)
            logging.info("SendGrid client initialized successfully")
        except KeyError:
            logging.error("SENDGRID_API_KEY not found in environment variables")
            raise
        except Exception as e:
            logging.error(f"Failed to initialize SendGrid client: {str(e)}")
            raise

        if match:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="Image Match Found",
                plain_text_content=f"Matching JPG: {match} found for {myblob.name}. CSV generated: {csv_blob_name}.")
            logging.info(f"Attempting to send match email for: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found",
                plain_text_content=f"No matching JPG found for {myblob.name} with a hash of {tiff_hash}. CSV generated: {csv_blob_name}.")
            logging.info("Attempting to send no-match email")

        try:
            sg.send(message)
            logging.info("Email sent successfully")
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise

    except Exception as e:
        logging.error(f"Critical failure in TiffUploadTrigger: {str(e)}")
        raise