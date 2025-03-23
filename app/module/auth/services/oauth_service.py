from os import getenv

import httpx
from dotenv import load_dotenv
from fastapi import status
from google.auth.transport import requests
from google.oauth2 import id_token

from app.module.auth.exceptions import (
    InvalidGoogleTokenException,
    InvalidKakaoTokenException,
    InvalidNaverTokenException,
    MissingEmailException,
    MissingSocialIDException,
)

load_dotenv()

GOOGLE_CLIENT_ID = getenv("GOOGLE_CLIENT_ID", None)
KAKAO_TOKEN_INFO_URL = getenv("KAKAO_TOKEN_INFO_URL", None)
NAVER_USER_INFO_URL = getenv("NAVER_USER_INFO_URL", None)


class NaverService:
    @classmethod
    async def verify_token(cls, token: str) -> tuple[str, str]:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(NAVER_USER_INFO_URL, headers=headers)

            if response.status_code is not status.HTTP_200_OK:
                raise InvalidNaverTokenException()

            id_info = response.json()
            social_id = id_info["response"].get("id")
            user_email = id_info["response"].get("email")

            if social_id is None:
                raise MissingSocialIDException()

            if user_email is None:
                raise MissingEmailException()

            return social_id, user_email


class KakaoService:
    @classmethod
    async def verify_token(cls, id_token: str) -> tuple[str, str]:
        data = {"id_token": id_token}
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
        async with httpx.AsyncClient() as client:
            response = await client.post(KAKAO_TOKEN_INFO_URL, data=data, headers=headers)
            if response.status_code is not status.HTTP_200_OK:
                raise InvalidKakaoTokenException()

            id_info: dict = response.json()
            social_id = id_info.get("sub", None)
            user_email = id_info.get("email", None)

            if social_id is None:
                raise MissingSocialIDException

            if user_email is None:
                raise MissingEmailException()

            return social_id, user_email


class GoogleService:
    @classmethod
    async def verify_token(cls, token: str) -> tuple[str, str]:
        try:
            id_info: dict = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            social_id = id_info.get("sub", None)
            user_email = id_info.get("email", None)
            if social_id is None:
                raise MissingSocialIDException()

            if user_email is None:
                raise MissingEmailException()

            return social_id, user_email
        except ValueError:
            raise InvalidGoogleTokenException()
