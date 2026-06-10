from fastapi import HTTPException
from typing import Optional


class APIException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400, details: Optional[dict] = None):
        super().__init__(status_code=status_code, detail=detail)
        self.details = details


def unified_error_handler(message: str) -> dict:
    return {"status": "error", "message": message}
