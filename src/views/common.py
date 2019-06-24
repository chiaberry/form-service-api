import os, json, boto3
from flask import Blueprint, request, redirect

from services.helpers import generate_clean_filename, generate_random_hash, is_valid_uniqueid

if (os.getenv("DEPLOYMENT_MODE") == "local"):
    # Initialize S3 Client
    s3 = boto3.client("s3",region_name=os.getenv("DEFALUT_REGION"), aws_access_key_id=os.getenv("S3_KEY"), aws_secret_access_key=os.getenv("S3_SECRET"))
else:
    # We should already have access to these resources
    s3 = boto3.client("s3", region_name=os.getenv("DEFALUT_REGION"))

bp = Blueprint('common', __name__)

@bp.route('/', methods=('GET',))
def index():
    return "Hello, world!", 200

@bp.route('/uploads/request-signature', methods=('GET',))
def uploads_request_signature():
    filename = request.args.get('file')
    uniqueid = str(request.args.get('uniqueid')).lower()

    if(str(filename) == "None" or filename == ""):
        return json.dumps({ "status": "error", "message": "file not declared"}), 403
    if(str(uniqueid) == "None" or filename == ""):
        return json.dumps({ "status": "error", "message": "case number not declared"}), 403
    if(is_valid_uniqueid(uniqueid) == False):
        return json.dumps({ "status": "error", "message": "invalid unique id: " + uniqueid + " (it must be a 64-char alphanumeric hash)"}), 403

    new_filename = generate_clean_filename(filename)
    new_key = "uploads/" + uniqueid + "/" + new_filename

    post = s3.generate_presigned_post(
        Bucket=os.getenv("S3_UPLOADS_BUCKET"),
        Key=new_key
    )

    response = {
        "status": "success",
        "message": "permission granted",
        "uuid": generate_random_hash(),
        "filename": filename,
        "creds": post
    }

    return json.dumps(response), 200

# Used in email templates.
# Creates link to download attachments sent by form
@bp.route('/file/download/<path:path>', methods=('GET',))
def file_download_uri(path):
    url = s3.generate_presigned_url(
        ExpiresIn=60, # seconds
        ClientMethod='get_object',
        Params={
            'Bucket': os.getenv("S3_UPLOADS_BUCKET"),
            'Key': path
        }
    )

    return redirect(url, code=302)
