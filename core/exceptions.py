from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from chat_app.app.core.response import ApiResponse

def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            status=False,
            status_code=exc.status_code,
            message=exc.detail,
            data=None,
        ).dict(),
    )
