from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Path
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os
import uuid
import shutil
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router para endpoints de imágenes
router = APIRouter(prefix="/api", tags=["Image Processing"])

# Ensure data directories exist
os.makedirs("./data/uploads", exist_ok=True)
os.makedirs("./data/results", exist_ok=True)

# Almacenamiento compartido para sesiones activas (se sustituirá por DB)
active_sessions = {}

# Clase de respuesta para análisis de imágenes
class AnalysisResponse(BaseModel):
    image_id: str
    metadata: Optional[Dict[str, Any]] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    geo_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Clase para la solicitud de chat
class ChatRequest(BaseModel):
    image_id: str
    message: str

@router.post("/upload/image", response_model=Dict[str, Any])
async def upload_image(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Endpoint para subir una imagen para análisis.
    
    Args:
        file: Archivo de imagen subido
        background_tasks: Tareas en segundo plano para procesamiento
        
    Returns:
        Diccionario con ID de imagen y ruta
    """
    try:
        # Validar tipo de archivo
        content_type = file.content_type
        if not content_type or not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")
        
        # Generar ID único y construir ruta
        image_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image_id}_{file.filename}"
        file_path = os.path.join("./data/uploads", filename)
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Imagen subida correctamente: {file_path}")
        
        # Registrar sesión activa
        active_sessions[image_id] = {
            "id": image_id,
            "filename": filename,
            "path": file_path,
            "type": "image",
            "status": "uploaded",
            "timestamp": time.time(),
            "metadata": {},
            "analysis": {}
        }
        
        # Iniciar análisis en segundo plano si se proporciona
        if background_tasks:
            background_tasks.add_task(analyze_image_task, image_id, file_path)
            active_sessions[image_id]["status"] = "processing"
        
        return {
            "success": True,
            "image_id": image_id,
            "filename": filename,
            "path": file_path
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al subir imagen: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")

@router.post("/analyze/image/{image_id}", response_model=AnalysisResponse)
async def analyze_image(image_id: str = Path(..., description="ID de la imagen a analizar"), 
                       detect_objects: bool = False):
    """
    Analiza una imagen previamente subida.
    
    Args:
        image_id: ID de la imagen
        detect_objects: Detectar objetos en la imagen
        
    Returns:
        Resultados del análisis
    """
    try:
        logger.info(f"Solicitando análisis de imagen: {image_id}")
        
        # Verificar si la imagen existe
        if image_id not in active_sessions:
            raise HTTPException(status_code=404, detail=f"Imagen no encontrada: {image_id}")
        
        session = active_sessions[image_id]
        file_path = session.get("path")
        
        # Verificar ruta del archivo
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Archivo de imagen no encontrado")
        
        # Ejecutar análisis (simulado por ahora)
        # En una implementación real, aquí se llamaría a servicios de análisis
        
        # Actualizar estado
        session["status"] = "analyzing"
        
        # Simular análisis de metadatos
        metadata = {
            "filename": session.get("filename", ""),
            "timestamp": datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path),
            "dimensions": "1920x1080"  # En una implementación real, se obtendría de la imagen
        }
        
        # Simular análisis de visión
        llm_analysis = {
            "description": "Imagen de un dron volando sobre un área urbana",
            "confidence": "medium"
        }
        
        # Simular datos de geolocalización
        geo_data = {
            "country": "Estados Unidos",
            "city": "Nueva York",
            "coordinates": {
                "latitude": 40.7128,
                "longitude": -74.0060
            },
            "confidence": "medium"
        }
        
        # Guardar resultados en la sesión
        session["metadata"] = metadata
        session["llm_analysis"] = llm_analysis
        session["geo_data"] = geo_data
        session["status"] = "completed"
        session["completed_at"] = time.time()
        
        # Procesar objetos si se solicita
        if detect_objects:
            # Esta parte se implementaría en una versión real
            # Aquí se delegaría al servicio de detección de objetos
            session["object_detection"] = {
                "status": "pending",
                "message": "La detección de objetos se procesará en segundo plano"
            }
        
        logger.info(f"Análisis completado para imagen: {image_id}")
        
        # Devolver resultados
        return AnalysisResponse(
            image_id=image_id,
            metadata=metadata,
            llm_analysis=llm_analysis,
            geo_data=geo_data
        )
        
    except HTTPException as e:
        logger.error(f"Error HTTP en analyze_image: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error en analyze_image: {str(e)}")
        return AnalysisResponse(
            image_id=image_id,
            error=str(e)
        )

@router.get("/session/{session_id}", response_model=Dict[str, Any])
async def get_session(session_id: str):
    """
    Obtiene detalles de una sesión.
    
    Args:
        session_id: ID de la sesión
        
    Returns:
        Detalles de la sesión
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail=f"Sesión no encontrada: {session_id}")
        
        return active_sessions[session_id]
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al obtener sesión: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener sesión: {str(e)}")

# Esta función se trasladará posteriormente al servicio correspondiente
def analyze_image_task(image_id: str, file_path: str):
    """Tarea en segundo plano para analizar una imagen."""
    try:
        logger.info(f"Iniciando análisis de imagen: {image_id}")
        
        # Actualizar estado
        if image_id in active_sessions:
            active_sessions[image_id]["status"] = "analyzing"
        
        # Análisis se implementará con el patrón de servicio
        # Por ahora, solo actualizamos el estado
        
        logger.info(f"Análisis de imagen completado: {image_id}")
        
        # Actualizar estado
        if image_id in active_sessions:
            active_sessions[image_id]["status"] = "completed"
            active_sessions[image_id]["completed_at"] = time.time()
            
    except Exception as e:
        logger.error(f"Error en analyze_image_task: {str(e)}")
        if image_id in active_sessions:
            active_sessions[image_id]["status"] = "error"
            active_sessions[image_id]["error"] = str(e)

@router.post("/chat/image/{image_id}", response_model=Dict[str, Any])
async def chat_with_image(image_id: str, request: ChatRequest):
    """
    Permite chatear sobre una imagen previamente subida.
    
    Args:
        image_id: ID de la imagen
        request: Solicitud con el mensaje del usuario
        
    Returns:
        Respuesta del chat
    """
    try:
        message = request.message
        logger.info(f"Chat sobre imagen: {image_id}, mensaje: {message}")
        
        # Verificar si la imagen existe
        if image_id not in active_sessions:
            raise HTTPException(status_code=404, detail=f"Imagen no encontrada: {image_id}")
        
        session = active_sessions[image_id]
        file_path = session.get("path")
        
        # Verificar ruta del archivo
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Archivo de imagen no encontrado")
        
        # Simular respuesta de chat
        # En una implementación real, esto se delegaría al servicio de visión LLM
        
        # Construir respuesta basada en mensaje del usuario
        response = ""
        if "ubicación" in message.lower() or "donde" in message.lower() or "lugar" in message.lower():
            response = "Esta imagen parece mostrar un área urbana de Nueva York, posiblemente Manhattan, basándome en los patrones de edificios y calles."
        elif "dron" in message.lower() or "drone" in message.lower():
            response = "La imagen muestra un dron tipo cuadricóptero, probablemente capturando imágenes aéreas de la ciudad."
        elif "edificio" in message.lower() or "altura" in message.lower():
            response = "Los edificios en la imagen son rascacielos típicos de Manhattan, con alturas que varían entre 100 y 300 metros aproximadamente."
        else:
            response = "La imagen muestra una vista aérea urbana tomada por un dron. Puedo ver edificios, calles y algunos espacios abiertos. ¿Hay algo específico que quieras saber sobre esta imagen?"
        
        # Registrar la conversación en la sesión
        if "conversations" not in session:
            session["conversations"] = []
            
        session["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "response": response
        })
        
        logger.info(f"Respuesta de chat generada para imagen: {image_id}")
        
        return {
            "success": True,
            "image_id": image_id,
            "message": message,
            "response": response
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error en chat_with_image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar chat sobre imagen: {str(e)}") 