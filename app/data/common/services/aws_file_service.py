import os

import boto3
from dotenv import find_dotenv, load_dotenv
from icecream import ic

from app.data.common.config import ENVIRONMENT
from database.enum import EnvironmentType

load_dotenv(find_dotenv())

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client("s3")


class AwsFileReader:
    @classmethod
    def _get_path(cls, filepath, bucket) -> str:
        if ENVIRONMENT == EnvironmentType.DEV:
            return filepath
        else:
            return cls._download_and_get_path(filepath, bucket)

    @classmethod
    def _download_and_get_path(cls, s3_key, bucket) -> str:
        local_path = f"/tmp/{os.path.basename(s3_key)}"

        cls._download_file_from_s3(bucket, s3_key, local_path)  # type: ignore
        return local_path

    @classmethod
    def _download_file_from_s3(cls, bucket: str, key: str, local_path: str) -> str:
        try:
            s3_client.download_file(bucket, key, local_path)
            return local_path
        except Exception as e:
            ic(f"Unexpected error: {e}")
            raise
