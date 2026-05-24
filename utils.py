from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from models.schemas import ErrorResponse


def success_response(data, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "status_code": status_code,
            "data": jsonable_encoder(data),
        },
    )


def error_response(status_code: int, error: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "status_code": status_code,
            "error": error,
        },
    )


# Dict reutilizable para documentar errores en los decoradores de cada router
ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}
