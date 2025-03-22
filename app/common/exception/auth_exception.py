from starlette import status

from app.common.enums import JWTErrorCode
from app.common.exception.base import AppException


class InvalidTokenException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 JWT 토큰입니다.", code=JWTErrorCode.INVALID_JWT_TOKEN
        )


class UserIDMissingException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JWT에 user ID 정보가 없습니다.",
            code=JWTErrorCode.JWT_USER_ID_MISSING,
        )
