"""
Configuración centralizada de rutas para la API de Drone-OSINT-GeoSpy.
Este módulo registra todos los controladores de la aplicación.
"""

from fastapi import APIRouter
import logging

# Importar controladores
from src.backend.controllers.image_controller import router as image_router
from src.backend.controllers.geo_controller import router as geo_router
from src.backend.controllers.detection_controller import router as detection_router
from src.backend.controllers.video_controller import router as video_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router principal
main_router = APIRouter()

# Registrar controladores
main_router.include_router(image_router)
main_router.include_router(geo_router)
main_router.include_router(detection_router)
main_router.include_router(video_router)

# Registro de rutas
logger.info("Rutas API configuradas:")
for route in main_router.routes:
    logger.info(f"  {route.path} [{', '.join(route.methods)}]") 