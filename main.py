import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from routers import companies, personas, campaigns, interactions, messages, reports, call_details, interaction_scores
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils import error_response

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="AuditBot API",
    description="API MVP Hackathon - Gestión de Campañas",
    version="1.0.0"
)

# Configurar CORS (útil para que el frontend no tenga bloqueos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Errores de validación de Pydantic (422) — campos faltantes o tipos incorrectos."""
    fields = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err["loc"] if l != "body")
        fields.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return error_response(422, f"Datos inválidos: {', '.join(fields)}")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTPExceptions lanzadas explícitamente (404, 400, etc.)."""
    return error_response(exc.status_code, exc.detail)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Cualquier error inesperado — en DEBUG muestra el detalle, en producción lo oculta."""
    detail = f"{type(exc).__name__}: {str(exc)}" if DEBUG else "Error interno del servidor"
    return error_response(500, detail)

# --- Routers ---

app.include_router(companies.router)
app.include_router(personas.router)
app.include_router(campaigns.router)
app.include_router(interactions.router)
app.include_router(messages.router)
app.include_router(call_details.router)
app.include_router(interaction_scores.router)
app.include_router(reports.router)

@app.get("/")
def read_root():
    return {"message": "AuditBot API funcionando al 100% 🚀"}

