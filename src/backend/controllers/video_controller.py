from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Path, Form
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import os
import uuid
import shutil
import logging
from datetime import datetime
import time
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router para endpoints de video
router = APIRouter(prefix="/api", tags=["Video Processing"])

# Ensure data directories exist
os.makedirs("./data/uploads", exist_ok=True)
os.makedirs("./data/frames", exist_ok=True)
os.makedirs("./data/results", exist_ok=True)

# Almacenamiento compartido para sesiones activas (se sustituirá por DB)
active_video_sessions = {}
active_streams = {}

@router.post("/upload/video", response_model=Dict[str, Any])
async def upload_video(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Endpoint para subir un video para análisis.
    
    Args:
        file: Archivo de video subido
        background_tasks: Tareas en segundo plano para procesamiento
        
    Returns:
        Diccionario con ID de video y ruta
    """
    try:
        # Validar tipo de archivo
        content_type = file.content_type
        if not content_type or not content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="El archivo debe ser un video")
        
        # Generar ID único y construir ruta
        video_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{video_id}_{file.filename}"
        file_path = os.path.join("./data/uploads", filename)
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Video subido correctamente: {file_path}")
        
        # Extraer información básica del video
        cap = cv2.VideoCapture(file_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        # Registrar sesión activa
        active_video_sessions[video_id] = {
            "id": video_id,
            "filename": filename,
            "path": file_path,
            "type": "video",
            "status": "uploaded",
            "timestamp": time.time(),
            "metadata": {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration": duration,
                "resolution": f"{width}x{height}"
            },
            "frames": []
        }
        
        # Iniciar extracción de fotogramas en segundo plano si se proporciona
        if background_tasks:
            background_tasks.add_task(extract_video_frames_task, video_id, file_path)
            active_video_sessions[video_id]["status"] = "processing"
        
        return {
            "success": True,
            "video_id": video_id,
            "filename": filename,
            "path": file_path,
            "metadata": {
                "fps": fps,
                "frame_count": frame_count,
                "duration": duration,
                "resolution": f"{width}x{height}"
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al subir video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar el video: {str(e)}")

@router.post("/stream/connect", response_model=Dict[str, Any])
async def connect_stream(stream_url: str = Form(...)):
    """
    Conecta a un flujo de video en tiempo real.
    
    Args:
        stream_url: URL del flujo de video (RTSP, HTTP, etc.)
        
    Returns:
        Diccionario con ID del flujo
    """
    try:
        # Validar URL (implementación básica)
        if not stream_url.startswith(('rtsp://', 'http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL de flujo inválida")
        
        # Generar ID único
        stream_id = str(uuid.uuid4())
        
        # Verificar conexión (simulado)
        # En una implementación real, se verificaría la conexión al flujo
        
        # Registrar flujo activo
        active_streams[stream_id] = {
            "id": stream_id,
            "url": stream_url,
            "status": "connected",
            "timestamp": time.time(),
            "frames": {},
            "latest_frame_path": None
        }
        
        logger.info(f"Conectado a flujo: {stream_url}, ID: {stream_id}")
        
        return {
            "success": True,
            "stream_id": stream_id,
            "url": stream_url,
            "status": "connected"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al conectar al flujo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al conectar al flujo: {str(e)}")

@router.post("/stream/disconnect/{stream_id}", response_model=Dict[str, Any])
async def disconnect_stream(stream_id: str):
    """
    Desconecta un flujo de video.
    
    Args:
        stream_id: ID del flujo
        
    Returns:
        Confirmación de desconexión
    """
    try:
        if stream_id not in active_streams:
            raise HTTPException(status_code=404, detail=f"Flujo no encontrado: {stream_id}")
        
        # Actualizar estado
        active_streams[stream_id]["status"] = "disconnected"
        
        logger.info(f"Desconectado del flujo: {stream_id}")
        
        return {
            "success": True,
            "stream_id": stream_id,
            "status": "disconnected"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al desconectar del flujo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al desconectar del flujo: {str(e)}")

@router.get("/stream/latest-frame/{stream_id}", response_model=Dict[str, Any])
async def get_latest_frame(stream_id: str, analyze: bool = False):
    """
    Obtiene el último fotograma de un flujo de video.
    
    Args:
        stream_id: ID del flujo
        analyze: Si se debe analizar el fotograma
        
    Returns:
        Información del fotograma capturado
    """
    try:
        if stream_id not in active_streams:
            raise HTTPException(status_code=404, detail=f"Flujo no encontrado: {stream_id}")
        
        stream = active_streams[stream_id]
        
        # En una implementación real, aquí se capturaría un fotograma del flujo
        # Por ahora, simulamos la captura
        
        # Simulación de captura
        frame_id = str(uuid.uuid4())
        timestamp = time.time()
        frame_path = f"./data/frames/stream_{stream_id}_{int(timestamp)}.jpg"
        
        # Simulamos la información del fotograma
        frame_info = {
            "id": frame_id,
            "timestamp": timestamp,
            "path": frame_path,
            "analyzed": False,
            "analysis": None
        }
        
        # Guardar referencia al fotograma
        stream["frames"][frame_id] = frame_info
        stream["latest_frame_path"] = frame_path
        
        # Analizar fotograma si se solicita
        if analyze:
            # En una implementación real, aquí se analizaría el fotograma
            # Por ahora, simulamos el análisis
            
            # Simular análisis
            frame_info["analyzed"] = True
            frame_info["analysis"] = {
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "resolution": "1920x1080"
                },
                "llm_analysis": {
                    "description": "Fotograma de video mostrando un área urbana",
                    "confidence": "medium"
                },
                "geo_data": {
                    "country": "Estados Unidos",
                    "city": "Nueva York",
                    "coordinates": {
                        "latitude": 40.7128,
                        "longitude": -74.0060
                    }
                }
            }
        
        logger.info(f"Capturado fotograma del flujo: {stream_id}")
        
        return {
            "success": True,
            "stream_id": stream_id,
            "frame_id": frame_id,
            "timestamp": timestamp,
            "frame_path": frame_path,
            "analyzed": frame_info["analyzed"],
            "analysis": frame_info["analysis"] if frame_info["analyzed"] else None
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al obtener fotograma: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener fotograma: {str(e)}")

# Funciones de utilidad
def extract_video_frames_task(video_id: str, file_path: str):
    """
    Tarea en segundo plano para extraer fotogramas de un video.
    
    Args:
        video_id: ID del video
        file_path: Ruta del archivo de video
    """
    try:
        logger.info(f"Iniciando extracción de fotogramas para video: {video_id}")
        
        # Verificar estado
        if video_id not in active_video_sessions:
            logger.error(f"Sesión de video no encontrada: {video_id}")
            return
        
        session = active_video_sessions[video_id]
        session["status"] = "extracting_frames"
        
        # Abrir video
        cap = cv2.VideoCapture(file_path)
        
        # Obtener información
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calcular intervalo para extraer fotogramas (1 por segundo)
        interval = int(fps) if fps > 0 else 30
        
        # Crear directorio para fotogramas
        frames_dir = f"./data/frames/{video_id}"
        os.makedirs(frames_dir, exist_ok=True)
        
        # Extraer fotogramas
        current_frame = 0
        extracted_frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
                
            if current_frame % interval == 0:
                # Guardar fotograma
                frame_id = f"{video_id}_frame_{current_frame}"
                frame_path = f"{frames_dir}/frame_{current_frame:06d}.jpg"
                cv2.imwrite(frame_path, frame)
                
                # Registrar fotograma
                frame_timestamp = current_frame / fps if fps > 0 else 0
                frame_info = {
                    "id": frame_id,
                    "frame_number": current_frame,
                    "timestamp": frame_timestamp,
                    "path": frame_path
                }
                
                extracted_frames.append(frame_info)
                
                logger.debug(f"Extraído fotograma {current_frame} del video {video_id}")
            
            current_frame += 1
            
            # Limitar a 100 fotogramas para este ejemplo
            if len(extracted_frames) >= 100:
                break
        
        # Cerrar video
        cap.release()
        
        # Actualizar sesión
        session["frames"] = extracted_frames
        session["status"] = "frames_extracted"
        session["frames_count"] = len(extracted_frames)
        
        logger.info(f"Extracción de fotogramas completada para video {video_id}: {len(extracted_frames)} fotogramas")
        
    except Exception as e:
        logger.error(f"Error en extract_video_frames_task: {str(e)}")
        
        # Actualizar estado en caso de error
        if video_id in active_video_sessions:
            active_video_sessions[video_id]["status"] = "extraction_error"
            active_video_sessions[video_id]["error"] = str(e) 