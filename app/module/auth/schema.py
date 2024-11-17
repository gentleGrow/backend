import re
from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.module.auth.enum import ProviderEnum, UserRoleEnum


class User(BaseModel):
    id: int
    social_id: str
    provider: ProviderEnum
    role: UserRoleEnum
    nickname: str | None
    created_at: datetime
    deleted_at: datetime | None


class AccessToken(BaseModel):
    exp: int
    user: int
    sub: str


class TokenRequest(BaseModel):
    id_token: str


class NicknameResponse(BaseModel):
    isUsed: bool


class NicknameRequest(BaseModel):
    nickname: str

    @staticmethod
    def validate_nickname(nickname: str):
        if len(nickname) < 2 or len(nickname) > 12:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="닉네임은 2자 이상 12자 이하여야 합니다.")

        if re.search(r"[^a-zA-Z0-9가-힣]", nickname):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="문자와 숫자만 가능합니다.")

        return nickname


class NaverTokenRequest(BaseModel):
    access_token: str


class UserDeleteRequest(BaseModel):
    reason: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str


class UserInfoResponse(BaseModel):
    nickname: str
    email: str
    isJoined: bool
