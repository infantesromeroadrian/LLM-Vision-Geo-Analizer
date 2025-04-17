from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos de datos para solicitudes
class ObjectDetectionRequest(BaseModel):
    image_id: str
    confidence: float = 0.25
    model: str = "xlarge"

# Crear router para endpoints de detección de objetos
router = APIRouter(prefix="/api", tags=["Object Detection"])

# Variable para simulación (se implementará con objeto de servicio)
available_models = ["nano", "small", "medium", "large", "xlarge"]
current_model = "xlarge"

@router.post("/detect/objects", response_model=Dict[str, Any])
async def detect_objects(request: ObjectDetectionRequest):
    """
    Detecta objetos en una imagen usando YOLOv8.
    
    Args:
        request: Solicitud con ID de imagen, umbral de confianza y modelo
        
    Returns:
        Diccionario con resultados de detección
    """
    try:
        # Validar ID de imagen
        if not request.image_id:
            raise HTTPException(status_code=400, detail="Se requiere ID de imagen")
        
        # Validar confianza
        if request.confidence < 0.1 or request.confidence > 1.0:
            raise HTTPException(
                status_code=400, 
                detail="El valor de confianza debe estar entre 0.1 y 1.0"
            )
        
        # Validar modelo
        if request.model not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"Modelo no válido. Opciones: {', '.join(available_models)}"
            )
        
        # Simular detección (será implementado con servicio)
        # En un caso real, aquí se buscaría la imagen por ID y se procesaría
        
        # Simular resultados de detección
        detection_results = {
            "success": True,
            "image_id": request.image_id,
            "model_used": request.model,
            "confidence_threshold": request.confidence,
            "detections": [
                {
                    "class": "persona",
                    "confidence": 0.92,
                    "bbox": [120, 80, 350, 420]
                },
                {
                    "class": "automóvil",
                    "confidence": 0.87,
                    "bbox": [450, 200, 650, 320]
                }
            ],
            "annotated_image_path": f"./data/results/{request.image_id}_annotated.jpg",
            "summary": {
                "total_objects_detected": 2,
                "object_counts": {
                    "persona": 1,
                    "automóvil": 1
                },
                "has_people": True,
                "most_common_object": "persona"
            }
        }
        
        # Simular creación de imagen anotada para el endpoint get_annotated_image
        # En implementación real, se crearía realmente el archivo
        
        return detection_results
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error en detección de objetos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en detección de objetos: {str(e)}")

@router.get("/image/annotated/{image_id}")
async def get_annotated_image(image_id: str):
    """
    Obtiene la imagen anotada con detecciones.
    
    Args:
        image_id: ID de la imagen
        
    Returns:
        Archivo de imagen anotada o error
    """
    try:
        # Construir ruta de archivo
        file_path = f"./data/results/{image_id}_annotated.jpg"
        
        # Verificar si existe (en implementación simulada siempre fallará)
        if not os.path.exists(file_path):
            # En implementación real, se manejaría adecuadamente
            # Por ahora, devolvemos error simulado
            raise HTTPException(
                status_code=404,
                detail=f"Imagen anotada no encontrada para ID: {image_id}"
            )
        
        # Devolver archivo
        return FileResponse(file_path)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al obtener imagen anotada: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener imagen anotada: {str(e)}")

@router.post("/set/model")
async def set_detection_model(model: str):
    """
    Establece el modelo de detección a utilizar.
    
    Args:
        model: Tipo de modelo (nano, small, medium, large, xlarge)
        
    Returns:
        Confirmación de cambio de modelo
    """
    try:
        # Validar modelo
        if model not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"Modelo no válido. Opciones: {', '.join(available_models)}"
            )
        
        # Actualizar modelo actual
        global current_model
        current_model = model
        
        return {
            "success": True,
            "message": f"Modelo establecido a: {model}",
            "current_model": model
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al establecer modelo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al establecer modelo: {str(e)}")

@router.get("/models")
async def get_available_models():
    """
    Obtiene lista de modelos de detección disponibles.
    
    Returns:
        Lista de modelos disponibles
    """
    try:
        return {
            "success": True,
            "available_models": available_models,
            "current_model": current_model
        }
        
    except Exception as e:
        logger.error(f"Error al obtener modelos disponibles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener modelos disponibles: {str(e)}") 