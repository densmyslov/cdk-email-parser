import json
import imaplib
import email
from email.utils import parsedate_to_datetime
from email.policy import default
from io import BytesIO
from datetime import datetime, timedelta, timezone, date
import boto3
from zipfile import ZipFile, ZIP_DEFLATED
import uuid
import ssl
import re
from PIL import Image, ExifTags
import imghdr
import os

BUCKET = os.environ.get('BUCKET')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # TODO implement
    
    print(event)
    # event is passed from invPar-email-parser-feeder
    client_email = event[0]
    print(f"client email: {client_email}")
    client_id = event[1]
    service_email = event[2]
    email_key = event[3]
    
    # Constants for IMAP connection
    IMAP_SSL_HOST = 'imap.gmail.com'
    IMAP_SSL_PORT = 993
    SSL_CONTEXT = None
    
    # includes 1 day: yesterday as at 12:00 UTC
    end_date_str = (datetime.now()).date().strftime("%d-%b-%Y") # new date at 12:00 UTC
    start_date_str = (datetime.now() - timedelta(days=1)).date().strftime("%d-%b-%Y") # yesterday 
    print(f"start_date: {start_date_str}, end_date: {end_date_str}")
    
    image_size = (500,500)
    
    # Collect PDF files from emails
    with imaplib.IMAP4_SSL(IMAP_SSL_HOST, IMAP_SSL_PORT, ssl_context=SSL_CONTEXT) as imap:
        imap.login(service_email, email_key)
        email_nums = fetch_emails(imap, start_date_str, end_date_str)
        print(f"number of emails: {len(email_nums)}")
        pdf_files, image_files = collect_attachments(imap, email_nums, 
                                                 image_size=image_size)
        print(f"Total PDFs collected: {len(pdf_files)}")
        print(f"Total images collected: {len(image_files)}")
        
    if len(pdf_files) > 0:
        
        # Create a ZIP file from PDF files
        zip_filename = '/tmp/pdf_attachments.zip' # Lambda's writable /tmp directory 512 Mb limit
        create_zip(pdf_files, zip_filename)
        
        # Set S3 parameters
        
        file_uid = uuid.uuid4().hex
        s3_key = f"accounts/{client_id}/zip/{file_uid}/zipped_email_pdfs_v1.zip"
        tags = ''
        metadata = {'tags': tags, 'customer_id': client_id, 
                    'source': client_email, 'start_date': start_date_str, 'end_date':end_date_str}
        
    
        # Upload the ZIP file to S3
        upload_to_s3(zip_filename, BUCKET, s3_key, metadata)
        print(f"ZIP file '{zip_filename}' uploaded to S3 bucket '{BUCKET}' with key '{s3_key}'")
        
    else:
        print("nothing to upload, no pdf files found")
    
    if len(image_files) > 0:
        zip_filename = '/tmp/image_attachments.zip' # Lambda's writable /tmp directory 512 Mb limit
        create_zip(image_files, zip_filename)
        
        file_uid = uuid.uuid4().hex
        s3_key = f"accounts/{client_id}/zip/{file_uid}/zipped_email_images_v1.zip"
        tags = ''
        metadata = {'tags': tags, 'customer_id': client_id, 
                    'source': client_email, 'start_date': start_date_str, 'end_date':end_date_str}
        
        # Upload the ZIP file to S3
        upload_to_s3(zip_filename, BUCKET, s3_key, metadata)
        print(f"ZIP file '{zip_filename}' uploaded to S3 bucket '{BUCKET}' with key '{s3_key}'")
    
    else:
        print("nothing to upload, no image files found")
    
    
    
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

#==============================FUNCTIONS========================================
# Function to fetch and parse emails
def fetch_emails(imap, start_date_str, end_date_str):
    imap.select('INBOX')
    type, data = imap.search(None, f'(SINCE "{start_date_str}" BEFORE "{end_date_str}")')
    return data[0].split()

def process_email(imap, num):
    typ, msg_data = imap.fetch(num, '(RFC822)')
    pdf_attachments = []
    image_attachments = []
    
    if typ == 'OK':
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1], policy=email.policy.default)
                email_date = parsedate_to_datetime(msg['Date']).strftime("%Y-%m-%d")
                
                for part in msg.walk():
                    if part.get_content_maintype() == 'application' or part.get_content_maintype() == 'image':
                        filename = part.get_filename()
                        if filename:
                            if filename.lower().endswith('.pdf'):
                                pdf_attachments.append((email_date, filename, part))
                            elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                                image_attachments.append((email_date, filename, part))
    
    return pdf_attachments, image_attachments


# Function to create a ZIP file from PDF files
def create_zip(pdf_files, zip_filename):
    with ZipFile(zip_filename, 'w') as zipf:
        for pdf_file in pdf_files:
            zipf.writestr(pdf_file.name, pdf_file.read())

# Function to upload the ZIP file to S3
def upload_to_s3(zip_filename, bucket_name, s3_key, metadata):

    with open(zip_filename, 'rb') as f:
        s3_client.upload_fileobj(f, bucket_name, s3_key, ExtraArgs={'Metadata': metadata})


def apply_exif_orientation(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())

        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Cases: image don't have getexif
        pass
    return image

def collect_attachments(imap, email_nums, image_size=None):
    pdf_files = []
    image_files = []
    seen_files = set()

    for num in email_nums:
        pdf_attachments, image_attachments = process_email(imap, num)

        # Process PDF attachments
        for email_date, filename, part in pdf_attachments:
            file_name = f"{email_date}_{filename}"
            if file_name not in seen_files:
                seen_files.add(file_name)
                content = part.get_payload(decode=True)
                file = BytesIO(content)
                file.name = file_name
                pdf_files.append(file)

        # Process image attachments
        for email_date, filename, part in image_attachments:
            file_name = f"{email_date}_{filename}"
            if file_name not in seen_files:
                seen_files.add(file_name)
                content = part.get_payload(decode=True)

                try:
                    img_bytes = BytesIO(content)
                    img_format = imghdr.what(img_bytes) or 'JPEG'  # Default to JPEG if unknown
                    img = Image.open(img_bytes)

                    # Apply EXIF orientation
                    img = apply_exif_orientation(img)

                    if image_size:
                        img = img.resize(image_size, Image.LANCZOS)

                    resized_content = BytesIO()
                    img.save(resized_content, format=img_format.upper())
                    content = resized_content.getvalue()
                    
                    file = BytesIO(content)
                    file.name = file_name
                    image_files.append(file)
                except Exception as e:
                    print(f"Error processing image {file_name}: {str(e)}")

    return pdf_files, image_files