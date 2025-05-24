#Function worked but didn't write (3rd or fourth time), Function app does have write permission to the blob.  
import logging
import azure.functions as func
from PIL import Image
import imagehash
import io
from azure.storage.blob import BlobServiceClient
import numpy as np  # Still needed for array conversion
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

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
            tiff_img_grey = tiff_img.convert("L")  # Force greyscale, works for RGB or greyscale
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(tiff_img_grey)  # Hash directly from greyscale
            logging.info(f"TIFF hash computed: {tiff_hash}")

        # Compare with hi-def-images
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None

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
                    jpg_img_grey = jpg_img.convert("L")  # Force greyscale, works for RGB or greyscale
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(jpg_img_grey)  # Hash directly from greyscale
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 15:  # Threshold for similarity
                        match = blob.name
                        logging.info(f"Match found: {match}")
                        # Append match to list.csv in hi-def-images container
                        append_blob_client = container_client.get_append_blob_client("list.csv")
                        append_blob_client.create_if_not_exists()
                        append_blob_client.append_block(f"{match},{myblob.name}\n")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue

        # Send email with enhanced logging
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
                plain_text_content=f"Matching JPG: {match} found for {myblob.name}.")
            logging.info(f"Attempting to send match email for: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found this time",
                plain_text_content=f"No matching JPG found for {myblob.name} with a hash of {tiff_hash}.  Thank you.")
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




###Final functional copy while testing OCR with basic OCR parts commented out.   

import logging
import azure.functions as func
from PIL import Image
import imagehash
import io
from azure.storage.blob import BlobServiceClient
import numpy as np  # Still needed for array conversion
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
#from azure.ai.vision import VisionServiceOptions, VisionSource, VisionAnalysisOptions, ImageAnalysisClient
#from azure.ai.vision import VisionServiceOptions, VisionSource, VisionAnalysisOptions, ImageAnalysisClient



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
            tiff_img_grey = tiff_img.convert("L")  # Force greyscale, works for RGB or greyscale
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(tiff_img_grey)  # Hash directly from greyscale
            logging.info(f"TIFF hash computed: {tiff_hash}")

        # Compare with hi-def-images
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None

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
                    jpg_img_grey = jpg_img.convert("L")  # Force greyscale, works for RGB or greyscale
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(jpg_img_grey)  # Hash directly from greyscale
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 15:  # Threshold for similarity
                        match = blob.name
                        logging.info(f"Match found: {match}")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue

        # Send email with enhanced logging
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
                plain_text_content=f"Matching JPG: {match} found for {myblob.name}.")
            logging.info(f"Attempting to send match email for: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found this time",
                plain_text_content=f"No matching JPG found for {myblob.name} with a hash of {tiff_hash}.  Thank you.")
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







#####   Try to include OCR from ImageAI object but fails with no stream log output!!!!!

import logging
import azure.functions as func
from PIL import Image
import imagehash
import io
from azure.storage.blob import BlobServiceClient
import numpy as np
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from azure.ai.vision import VisionServiceOptions, VisionSource, VisionAnalysisOptions, ImageAnalysisClient

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", path="low-def-tiffs/{name}", connection="AzureWebJobsStorage")
def TiffUploadTrigger(myblob: func.InputStream):
    logging.info(f"Triggered by blob: {myblob.name}")
    try:
        # Storage connection (unchanged)
        logging.info("Fetching connection string")
        conn_str = os.environ["AzureWebJobsStorage"]
        logging.info("Initializing BlobServiceClient")
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)

        # Extract first page of TIFF (unchanged)
        logging.info(f"Reading TIFF stream: {myblob.name}")
        tiff_data = myblob.read()
        logging.info(f"TIFF data read, length: {len(tiff_data)} bytes")
        tiff_stream = io.BytesIO(tiff_data)
        logging.info(f"Opening TIFF: {myblob.name}")
        with Image.open(tiff_stream) as tiff_img:
            logging.info(f"Seeking first page of TIFF: {myblob.name}")
            tiff_img.seek(0)
            logging.info(f"Converting TIFF to greyscale: {myblob.name}")
            tiff_img_grey = tiff_img.convert("L")  # Force greyscale for hashing
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(tiff_img_grey)  # Hash directly from greyscale
            logging.info(f"TIFF hash computed: {tiff_hash}")

            # OCR on second page of TIFF using Azure AI Vision
            logging.info(f"Seeking second page of TIFF: {myblob.name}")
            try:
                tiff_img.seek(1)  # Move to second page (index 1, 0-based)
                logging.info(f"Converting second page of TIFF for OCR: {myblob.name}")
                tiff_buffer = io.BytesIO()
                tiff_img.save(tiff_buffer, format="TIFF")  # Save second page as TIFF bytes
                tiff_buffer.seek(0)

                # Initialize Azure AI Vision client
                endpoint = os.environ["VISION_ENDPOINT"]  # Set in Function App settings
                key = os.environ["VISION_KEY"]  # Set in Function App settings
                client = ImageAnalysisClient(
                    endpoint=endpoint,
                    credential=key
                )

                # Analyze image for OCR (Read feature)
                vision_source = VisionSource(memory=tiff_buffer.read())
                analysis_options = VisionAnalysisOptions(features=["Read"])
                result = client.analyze(vision_source, analysis_options)

                # Extract text from Read result
                ocr_text = ""
                if result.read is not None:
                    for block in result.read.blocks:
                        for line in block.lines:
                            ocr_text += line.text + "\n"
                ocr_text = ocr_text.strip() or "No text found"
                logging.info(f"OCR extracted text: {ocr_text}")
            except EOFError:
                logging.warning(f"No second page found in TIFF: {myblob.name}")
                ocr_text = "No second page or text found"
            except Exception as e:
                logging.error(f"OCR failed for TIFF {myblob.name} with Azure AI Vision: {str(e)}")
                ocr_text = "OCR error occurred"

            # Email OCR results
            logging.info("Preparing to send OCR email")
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

        # Compare with hi-def-images (unchanged)
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None

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
                    jpg_img_grey = jpg_img.convert("L")  # Force greyscale
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(jpg_img_grey)  # Hash directly from greyscale
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 15:  # Threshold for similarity
                        match = blob.name
                        logging.info(f"Match found: {match}")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue

        # Send match/no-match email (unchanged)
        logging.info("Preparing to send match/no-match email")
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
                plain_text_content=f"Matching JPG: {match} found for {myblob.name}.  OCR text (second page): {ocr_text}. Thank you.")
            logging.info(f"Attempting to send match email for: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found this time",
                plain_text_content=f"No matching JPG found for {myblob.name} with a hash of {tiff_hash}. OCR text (second page): {ocr_text}. Thank you.")
            logging.info("Attempting to send no-match email")

        try:
            sg.send(message)
            logging.info("Match/no-match email sent successfully")
        except Exception as e:
            logging.error(f"Failed to send match/no-match email: {str(e)}")
            raise

    except Exception as e:
        logging.error(f"Critical failure in TiffUploadTrigger: {str(e)}")
        raise











###Working on greyscale, no OCR Support:

import logging
import azure.functions as func
from PIL import Image
import imagehash
import io
from azure.storage.blob import BlobServiceClient
import numpy as np  # Still needed for array conversion
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

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
            tiff_img_grey = tiff_img.convert("L")  # Force greyscale, works for RGB or greyscale
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(tiff_img_grey)  # Hash directly from greyscale
            logging.info(f"TIFF hash computed: {tiff_hash}")

        # Compare with hi-def-images
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None

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
                    jpg_img_grey = jpg_img.convert("L")  # Force greyscale, works for RGB or greyscale
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(jpg_img_grey)  # Hash directly from greyscale
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 15:  # Threshold for similarity
                        match = blob.name
                        logging.info(f"Match found: {match}")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue

        # Send email with enhanced logging
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
                plain_text_content=f"Matching JPG: {match} found for {myblob.name}.")
            logging.info(f"Attempting to send match email for: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found this time",
                plain_text_content=f"No matching JPG found for {myblob.name} with a hash of {tiff_hash}.  Thank you.")
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





########Fails on Greyscale
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
            logging.info(f"Converting TIFF to BGR: {myblob.name}")
            tiff_cv = cv2.cvtColor(np.array(tiff_img), cv2.COLOR_RGB2BGR)
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(Image.fromarray(tiff_cv))
            logging.info(f"TIFF hash computed: {tiff_hash}")

        # Compare with hi-def-images
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None

        for blob in blobs:
            try:
                logging.info(f"Processing blob: {blob.name}")
                blob_client = container_client.get_blob_client(blob.name)
                logging.info(f"Downloading JPG: {blob.name}")
                jpg_stream = blob_client.download_blob().readall()
                logging.info(f"JPG downloaded, length: {len(jpg_stream)} bytes")
                
                logging.info(f"Opening JPG: {blob.name}")
                with Image.open(io.BytesIO(jpg_stream)) as jpg_img:
                    logging.info(f"Converting JPG to BGR: {blob.name}")
                    jpg_cv = cv2.cvtColor(np.array(jpg_img), cv2.COLOR_RGB2BGR)
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(Image.fromarray(jpg_cv))
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 8:  # Threshold for similarity
                        match = blob.name
                        logging.info(f"Match found: {match}")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue

        # Send email with enhanced logging
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
                plain_text_content=f"Matching JPG: {match}")
            logging.info(f"Attempting to send match email for: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found this time",
                plain_text_content="No matching JPG found")
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
            logging.info(f"Converting TIFF to BGR: {myblob.name}")
            tiff_cv = cv2.cvtColor(np.array(tiff_img), cv2.COLOR_RGB2BGR)
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(Image.fromarray(tiff_cv))
            logging.info(f"TIFF hash computed: {tiff_hash}")

        # Compare with hi-def-images
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None

        for blob in blobs:
            try:
                logging.info(f"Processing blob: {blob.name}")
                blob_client = container_client.get_blob_client(blob.name)
                logging.info(f"Downloading JPG: {blob.name}")
                jpg_stream = blob_client.download_blob().readall()
                logging.info(f"JPG downloaded, length: {len(jpg_stream)} bytes")
                
                logging.info(f"Opening JPG: {blob.name}")
                with Image.open(io.BytesIO(jpg_stream)) as jpg_img:
                    logging.info(f"Converting JPG to BGR: {blob.name}")
                    jpg_cv = cv2.cvtColor(np.array(jpg_img), cv2.COLOR_RGB2BGR)
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(Image.fromarray(jpg_cv))
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 20:  # Threshold for similarity
                        match = blob.name
                        logging.info(f"Match found: {match}")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue

        # Send email
        logging.info("Preparing to send email")
        sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
        sg = SendGridAPIClient(sendgrid_api_key)
        
        if match:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="Image Match Found",
                plain_text_content=f"Matching JPG: {match}")
            logging.info(f"Sending match email for: {match}")
            sg.send(message)
            logging.info(f"Emailed match: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found this time",
                plain_text_content="No matching JPG found")
            logging.info("Sending no-match email")
            sg.send(message)
            logging.info("No match found.")

    except Exception as e:
        logging.error(f"Critical failure in TiffUploadTrigger: {str(e)}")
        raise













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

    try:
        # Storage connection
        logging.info("Connecting to Azure Storage")
        conn_str = os.environ["AzureWebJobsStorage"]
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)

        # Extract first page of TIFF
        logging.info(f"Reading TIFF stream: {myblob.name}")
        tiff_stream = io.BytesIO(myblob.read())
        logging.info(f"Opening TIFF: {myblob.name}")
        with Image.open(tiff_stream) as tiff_img:
            logging.info(f"Seeking first page of TIFF: {myblob.name}")
            tiff_img.seek(0)  # First page
            logging.info(f"Converting TIFF to BGR: {myblob.name}")
            tiff_cv = cv2.cvtColor(np.array(tiff_img), cv2.COLOR_RGB2BGR)
            logging.info(f"Computing TIFF hash: {myblob.name}")
            tiff_hash = imagehash.average_hash(Image.fromarray(tiff_cv))
            logging.info(f"TIFF hash computed: {tiff_hash}")

        # Compare with hi-def-images
        logging.info("Accessing hi-def-images container")
        container_client = blob_service_client.get_container_client("hi-def-images")
        blobs = container_client.list_blobs()
        match = None

        for blob in blobs:
            try:
                logging.info(f"Processing blob: {blob.name}")
                blob_client = container_client.get_blob_client(blob.name)
                logging.info(f"Downloading JPG: {blob.name}")
                jpg_stream = blob_client.download_blob().readall()
                
                logging.info(f"Opening JPG: {blob.name}")
                with Image.open(io.BytesIO(jpg_stream)) as jpg_img:
                    logging.info(f"Converting JPG to BGR: {blob.name}")
                    jpg_cv = cv2.cvtColor(np.array(jpg_img), cv2.COLOR_RGB2BGR)
                    logging.info(f"Computing JPG hash: {blob.name}")
                    jpg_hash = imagehash.average_hash(Image.fromarray(jpg_cv))
                    logging.info(f"JPG hash for {blob.name}: {jpg_hash}")

                    distance = tiff_hash - jpg_hash
                    logging.info(f"Hash distance between TIFF and {blob.name}: {distance}")
                    if distance < 20:  # Threshold for similarity
                        match = blob.name
                        logging.info(f"Match found: {match}")
                        break
            except Exception as e:
                logging.error(f"Error processing JPG {blob.name}: {str(e)}")
                continue  # Skip to next blob on failure

        # Send email
        logging.info("Preparing to send email")
        sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
        sg = SendGridAPIClient(sendgrid_api_key)
        
        if match:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="Image Match Found",
                plain_text_content=f"Matching JPG: {match}")
            logging.info(f"Sending match email for: {match}")
            sg.send(message)
            logging.info(f"Emailed match: {match}")
        else:
            message = Mail(
                from_email="no-reply@pwdi.net",
                to_emails="PictureScanner@pwdi.net",
                subject="NO Image Match Found this time",
                plain_text_content="No matching JPG found")
            logging.info("Sending no-match email")
            sg.send(message)
            logging.info("No match found.")

    except Exception as e:
        logging.error(f"Critical failure in TiffUploadTrigger: {str(e)}")
        raise  # Re-raise to ensure function fails and logs the error

















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
            if tiff_hash - jpg_hash < 20:  # Threshold for similarity
                match = blob.name
                break

    # Send email
    if match:
        sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
        message = Mail(
            from_email="no-reply@pwdi.net",
            to_emails="PictureScanner@pwdi.net",
            subject="Image Match Found",
            plain_text_content=f"Matching JPG: {match}")
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
        logging.info(f"Emailed match: {match}")
    else:
        sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
        message = Mail(
            from_email="no-reply@pwdi.net",
            to_emails="PictureScanner@pwdi.net",
            subject="NO Image Match Found this time",
            plain_text_content=f"Matching JPG: {match}")
        sg = SendGridAPIClient(sendgrid_api_key)
        sg.send(message)
        logging.info("No match found.")

