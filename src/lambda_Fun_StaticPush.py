import json
import base64
import zipfile
import io
import os
import mimetypes
import logging
import boto3
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

# YOUR BUCKET NAME
BUCKET_NAME = "staticpush-sites-project"
ROOT_PREFIX = "sites/"


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event)[:1000])

    try:
        # 1) Parse JSON body
        body_str = event.get("body")
        if not body_str:
            return _resp(400, {"error": "Missing request body"})

        try:
            body = json.loads(body_str)
        except:
            return _resp(400, {"error": "Body is not valid JSON"})

        zip_b64 = body.get("zip")
        if not zip_b64:
            return _resp(400, {"error": "Missing 'zip' field"})

        # 2) Decode base64 ZIP
        try:
            zip_bytes = base64.b64decode(zip_b64)
        except:
            return _resp(400, {"error": "Invalid base64 ZIP"})

        # 3) Generate unique site ID
        site_id = datetime.utcnow().strftime("site_%Y%m%d_%H%M%S")
        prefix = f"{ROOT_PREFIX}{site_id}/"

        # 4) Extract ZIP, find index.html, upload files
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
            names = z.namelist()

            # find index file inside zip
            index_candidates = [n for n in names if n.lower().endswith("index.html")]
            if not index_candidates:
                return _resp(400, {"error": "ZIP must contain index.html"})

            index_path_in_zip = index_candidates[0]  # e.g. "folder/index.html"

            # Upload all files
            for name in names:
                if name.endswith("/"):
                    continue

                file_data = z.read(name)
                key = prefix + name

                content_type, _ = mimetypes.guess_type(name)
                put_args = {
                    "Bucket": BUCKET_NAME,
                    "Key": key,
                    "Body": file_data
                }
                if content_type:
                    put_args["ContentType"] = content_type

                logger.info("Uploading to s3://%s/%s", BUCKET_NAME, key)
                s3.put_object(**put_args)

        # 5) Build correct website URL using index.html directory
        region = os.environ.get("AWS_REGION", "ap-south-1")
        base_url = f"http://{BUCKET_NAME}.s3-website.{region}.amazonaws.com"

        index_dir = os.path.dirname(index_path_in_zip)  # "" or "folder"

        if index_dir:
            # subfolder case
            site_url = f"{base_url}/{prefix}{index_dir}/"
        else:
            # index.html at root
            site_url = f"{base_url}/{prefix}"

        return _resp(200, {
            "message": "Deployment successful",
            "site_id": site_id,
            "url": site_url
        })

    except Exception as e:
        logger.exception("Unhandled error")
        return _resp(500, {"error": "Internal server error", "detail": str(e)})


def _resp(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body_dict)
    }

