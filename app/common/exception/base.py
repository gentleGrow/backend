from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str):
        super().__init__(
            status_code=status_code,
            detail={
                "message": detail,
                "code": code,
            },
        )
