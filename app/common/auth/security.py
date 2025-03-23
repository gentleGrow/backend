from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer

from app.common.dependencies.jwt_dependency import get_jwt_service
from app.common.exception.auth_exception import InvalidTokenException, UserIDMissingException
from app.common.services.jwt_service import JWTService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_jwt_token(
    encode_token: str = Security(oauth2_scheme), jwt_service: JWTService = Depends(get_jwt_service)
) -> dict:
    try:
        token: dict = jwt_service.decode_token(encode_token)
    except Exception:
        raise InvalidTokenException()

    user_id = token.get("user", None)
    if user_id is None:
        raise UserIDMissingException()
    return token
