"""
Sistema centralizado de manejo de errores para Drone-OSINT-GeoSpy.
Proporciona clases base para excepciones y funciones para manejo de errores.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import Dict, Any, Optional, Type, List, Callable
import traceback
import logging
import sys
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIException(Exception):
    """
    Excepción base para errores de API.
    Proporciona una estructura consistente para todos los errores.
    """
    
    def __init__(
        self, 
        status_code: int = 500, 
        error_code: str = "internal_error", 
        message: str = "Error interno del servidor",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción.
        
        Args:
            status_code: Código HTTP de respuesta
            error_code: Código de error para identificación
            message: Mensaje descriptivo del error
            details: Detalles adicionales del error
        """
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la excepción a un diccionario para respuesta JSON.
        
        Returns:
            Diccionario con información del error
        """
        error_dict = {
            "status": "error",
            "error_code": self.error_code,
            "message": self.message
        }
        
        if self.details:
            error_dict["details"] = self.details
            
        return error_dict

# Excepciones específicas comunes
class NotFoundError(APIException):
    """Excepción para recursos no encontrados."""
    
    def __init__(
        self, 
        message: str = "Recurso no encontrado", 
        resource_type: str = "resource",
        resource_id: Optional[str] = None,
        error_code: str = "not_found"
    ):
        """
        Inicializa la excepción de recurso no encontrado.
        
        Args:
            message: Mensaje descriptivo del error
            resource_type: Tipo de recurso no encontrado
            resource_id: ID del recurso no encontrado
            error_code: Código de error específico
        """
        details = {
            "resource_type": resource_type
        }
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            status_code=404,
            error_code=error_code,
            message=message,
            details=details
        )

class ValidationError(APIException):
    """Excepción para errores de validación."""
    
    def __init__(
        self, 
        message: str = "Error de validación", 
        field_errors: Optional[Dict[str, str]] = None,
        error_code: str = "validation_error"
    ):
        """
        Inicializa la excepción de error de validación.
        
        Args:
            message: Mensaje descriptivo del error
            field_errors: Errores por campo
            error_code: Código de error específico
        """
        details = {}
        if field_errors:
            details["field_errors"] = field_errors
            
        super().__init__(
            status_code=400,
            error_code=error_code,
            message=message,
            details=details
        )

class AuthorizationError(APIException):
    """Excepción para errores de autorización."""
    
    def __init__(
        self, 
        message: str = "No autorizado", 
        error_code: str = "unauthorized"
    ):
        """
        Inicializa la excepción de error de autorización.
        
        Args:
            message: Mensaje descriptivo del error
            error_code: Código de error específico
        """
        super().__init__(
            status_code=401,
            error_code=error_code,
            message=message
        )

class ForbiddenError(APIException):
    """Excepción para acciones prohibidas."""
    
    def __init__(
        self, 
        message: str = "Acceso prohibido", 
        error_code: str = "forbidden"
    ):
        """
        Inicializa la excepción de acceso prohibido.
        
        Args:
            message: Mensaje descriptivo del error
            error_code: Código de error específico
        """
        super().__init__(
            status_code=403,
            error_code=error_code,
            message=message
        )

class ServiceUnavailableError(APIException):
    """Excepción para servicios no disponibles."""
    
    def __init__(
        self, 
        message: str = "Servicio no disponible", 
        service: Optional[str] = None,
        error_code: str = "service_unavailable"
    ):
        """
        Inicializa la excepción de servicio no disponible.
        
        Args:
            message: Mensaje descriptivo del error
            service: Nombre del servicio no disponible
            error_code: Código de error específico
        """
        details = {}
        if service:
            details["service"] = service
            
        super().__init__(
            status_code=503,
            error_code=error_code,
            message=message,
            details=details
        )

class RateLimitError(APIException):
    """Excepción para límite de tasa excedido."""
    
    def __init__(
        self, 
        message: str = "Límite de tasa excedido", 
        reset_seconds: Optional[int] = None,
        error_code: str = "rate_limit_exceeded"
    ):
        """
        Inicializa la excepción de límite de tasa excedido.
        
        Args:
            message: Mensaje descriptivo del error
            reset_seconds: Segundos hasta reinicio del límite
            error_code: Código de error específico
        """
        details = {}
        if reset_seconds is not None:
            details["reset_in_seconds"] = reset_seconds
            
        super().__init__(
            status_code=429,
            error_code=error_code,
            message=message,
            details=details
        )

class BadRequestError(APIException):
    """Excepción para solicitudes incorrectas."""
    
    def __init__(
        self, 
        message: str = "Solicitud incorrecta", 
        error_code: str = "bad_request",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa la excepción de solicitud incorrecta.
        
        Args:
            message: Mensaje descriptivo del error
            error_code: Código de error específico
            details: Detalles adicionales del error
        """
        super().__init__(
            status_code=400,
            error_code=error_code,
            message=message,
            details=details
        )

# Manejadores de excepciones para FastAPI
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Manejador de APIException para FastAPI.
    
    Args:
        request: Objeto Request
        exc: Objeto APIException
        
    Returns:
        Respuesta JSON con información del error
    """
    # Registrar error en el log
    if exc.status_code >= 500:
        logger.error(
            f"API Error {exc.status_code} ({exc.error_code}): {exc.message}",
            exc_info=True
        )
    else:
        logger.warning(
            f"API Error {exc.status_code} ({exc.error_code}): {exc.message}"
        )
    
    # Devolver respuesta JSON
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Manejador de errores de validación de FastAPI.
    
    Args:
        request: Objeto Request
        exc: Objeto RequestValidationError
        
    Returns:
        Respuesta JSON con información del error
    """
    # Extraer errores de validación
    field_errors = {}
    for error in exc.errors():
        loc = ".".join([str(l) for l in error["loc"] if l != "body"])
        field_errors[loc] = error["msg"]
    
    # Crear excepción personalizada
    custom_exc = ValidationError(
        message="Error de validación en la solicitud",
        field_errors=field_errors
    )
    
    # Registrar error
    logger.warning(
        f"Validation Error: {custom_exc.message}",
        extra={"field_errors": field_errors}
    )
    
    # Devolver respuesta JSON
    return JSONResponse(
        status_code=custom_exc.status_code,
        content=custom_exc.to_dict()
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Manejador genérico para excepciones no controladas.
    
    Args:
        request: Objeto Request
        exc: Objeto Exception
        
    Returns:
        Respuesta JSON con información del error
    """
    # Obtener información del error
    error_detail = "".join(traceback.format_exception(
        type(exc), exc, exc.__traceback__
    ))
    
    # Ocultar detalles en producción
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    # Crear excepción personalizada
    custom_exc = APIException(
        status_code=500,
        error_code="internal_server_error",
        message="Error interno del servidor"
    )
    
    # Añadir detalles solo en desarrollo
    if not is_production:
        custom_exc.details = {
            "exception_type": exc.__class__.__name__,
            "exception_message": str(exc),
            "traceback": error_detail.split("\n")
        }
    
    # Registrar error
    logger.error(
        f"Unhandled Exception: {exc.__class__.__name__}: {str(exc)}",
        exc_info=True
    )
    
    # Devolver respuesta JSON
    return JSONResponse(
        status_code=custom_exc.status_code,
        content=custom_exc.to_dict()
    )

def configure_exception_handlers(app):
    """
    Configura manejadores de excepciones para una aplicación FastAPI.
    
    Args:
        app: Instancia de FastAPI
    """
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler) 