from pydantic import BaseModel, Field


class PostResponse(BaseModel):
    status_code: int = Field(..., description="상태 코드")
    detail: str


class PutResponse(BaseModel):
    status_code: int = Field(..., description="상태 코드")
    detail: str


class DeleteResponse(BaseModel):
    status_code: int = Field(..., description="상태 코드")
    detail: str

