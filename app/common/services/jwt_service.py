from datetime import datetime, timedelta, timezone
from os import getenv

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError, decode, encode

from app.module.auth.constant import JWT_ACCESS_TIME_MINUTE, JWT_REFRESH_TIME_MINUTE

load_dotenv()

JWT_SECRET_KEY = getenv("JWT_SECRET", None)
JWT_ALGORITHM = getenv("JWT_ALGORITHM", None)


class JWTService:
    def generate_access_token(self, user_id: str | int, social_id: str | int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TIME_MINUTE)
        payload = {"exp": expire, "user": str(user_id), "sub": str(social_id)}
        return encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def generate_refresh_token(self, user_id: str | int, social_id: str | int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_REFRESH_TIME_MINUTE)
        payload = {"exp": expire, "user": str(user_id), "sub": str(social_id)}
        return encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def decode_token(self, token: str) -> dict:
        try:
            return decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token이 만료되었습니다.")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 token입니다.")
