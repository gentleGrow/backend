from enum import StrEnum


class JWTErrorCode(StrEnum):
    INVALID_JWT_TOKEN = "INVALID_JWT_TOKEN"
    JWT_USER_ID_MISSING = "JWT_USER_ID_MISSING"
