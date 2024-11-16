import os
import boto3
import json

from botocore.exceptions import ClientError
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
from app.module.auth.constant import USER_QUIT_FILENAME

load_dotenv(find_dotenv())

s3_client = boto3.client("s3")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_USER_QUIT = os.getenv("S3_BUCKET_USER_QUIT", None)


class UserService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = S3_BUCKET_USER_QUIT

    async def save_user_quit_reason(self, reason: str) -> None:
        today = datetime.now().strftime("%Y%m%d")
        file_key = f"{USER_QUIT_FILENAME}_{today}.json"

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            file_content = response['Body'].read().decode('utf-8')
            reasons = json.loads(file_content) 
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                reasons = []
            else:
                raise

        reasons.append(reason)

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=json.dumps(reasons),
            ContentType='application/json'
        )
    
    
    
    
    
    