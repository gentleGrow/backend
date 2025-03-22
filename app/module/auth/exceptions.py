from fastapi import status

from app.common.exception.base import AppException
from app.module.auth.enum import AuthErrorCode


class InvalidGoogleTokenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 Google ID Token입니다.",
            code=AuthErrorCode.INVALID_GOOGLE_TOKEN,
        )


class InvalidNaverTokenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 Naver ID Token입니다.",
            code=AuthErrorCode.INVALID_NAVER_TOKEN,
        )


class InvalidKakaoTokenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 Kakao ID Token입니다.",
            code=AuthErrorCode.INVALID_KAKAO_TOKEN,
        )


class MissingSocialIDException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID Token에 유저 정보가 없습니다.",
            code=AuthErrorCode.MISSING_SOCIAL_ID,
        )


class MissingEmailException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="유저 이메일이 없습니다.", code=AuthErrorCode.MISSING_EMAIL
        )
