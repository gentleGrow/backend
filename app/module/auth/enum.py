from enum import StrEnum


class ProviderEnum(StrEnum):
    GOOGLE = "google"
    KAKAO = "kakao"
    NAVER = "naver"


class UserRoleEnum(StrEnum):
    ADMIN = "admin"
    USER = "user"


class AuthErrorCode(StrEnum):
    INVALID_GOOGLE_TOKEN = "INVALID_GOOGLE_TOKEN"
    INVALID_NAVER_TOKEN = "INVALID_NAVER_TOKEN"
    INVALID_KAKAO_TOKEN = "INVALID_KAKAO_TOKEN"
    MISSING_SOCIAL_ID = "MISSING_SOCIAL_ID"
    MISSING_EMAIL = "MISSING_EMAIL"
