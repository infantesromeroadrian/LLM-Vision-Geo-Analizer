"""
Módulo de base de datos para Drone-OSINT-GeoSpy.
Proporciona modelos ORM y funcionalidad de persistencia.
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, 
    DateTime, ForeignKey, JSON, Boolean, Text, inspect
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determinar URL de base de datos desde variables de entorno o usar SQLite por defecto
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./data/drone_osint.db")

# Crear base y motor de base de datos
Base = declarative_base()
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Analysis(Base):
    """Modelo para almacenar resultados de análisis de imágenes."""
    
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True)
    image_id = Column(String(36), unique=True, index=True)
    filename = Column(String(255))
    file_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="created")
    
    # Datos de análisis
    metadata = Column(JSON, nullable=True)
    llm_analysis = Column(JSON, nullable=True)
    geo_data = Column(JSON, nullable=True)
    
    # Coordenadas (almacenadas por separado para facilitar consultas)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    confidence = Column(String(50), nullable=True)
    
    # Relaciones
    detections = relationship("Detection", back_populates="analysis", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a un diccionario."""
        return {
            "id": self.id,
            "image_id": self.image_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "metadata": self.metadata,
            "llm_analysis": self.llm_analysis,
            "geo_data": self.geo_data,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude
            } if self.latitude and self.longitude else None,
            "country": self.country,
            "city": self.city,
            "confidence": self.confidence,
            "detections": [d.to_dict() for d in self.detections] if self.detections else []
        }

class Detection(Base):
    """Modelo para almacenar detecciones de objetos en una imagen."""
    
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    object_class = Column(String(100))
    confidence = Column(Float)
    bbox_x1 = Column(Integer)
    bbox_y1 = Column(Integer)
    bbox_x2 = Column(Integer)
    bbox_y2 = Column(Integer)
    
    # Relaciones
    analysis = relationship("Analysis", back_populates="detections")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a un diccionario."""
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "object_class": self.object_class,
            "confidence": self.confidence,
            "bbox": [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2]
        }

class VideoAnalysis(Base):
    """Modelo para almacenar análisis de videos."""
    
    __tablename__ = "video_analyses"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(36), unique=True, index=True)
    filename = Column(String(255))
    file_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="created")
    
    # Metadatos del video
    duration = Column(Float, nullable=True)
    frame_count = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    resolution = Column(String(50), nullable=True)
    
    # Relaciones
    frames = relationship("VideoFrame", back_populates="video", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a un diccionario."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "duration": self.duration,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "resolution": self.resolution,
            "frames": [f.to_dict() for f in self.frames] if self.frames else []
        }

class VideoFrame(Base):
    """Modelo para almacenar fotogramas extraídos de videos."""
    
    __tablename__ = "video_frames"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("video_analyses.id"))
    frame_number = Column(Integer)
    timestamp = Column(Float)
    file_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Análisis del fotograma
    analyzed = Column(Boolean, default=False)
    metadata = Column(JSON, nullable=True)
    llm_analysis = Column(JSON, nullable=True)
    geo_data = Column(JSON, nullable=True)
    
    # Coordenadas
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Relaciones
    video = relationship("VideoAnalysis", back_populates="frames")
    detections = relationship("FrameDetection", back_populates="frame", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a un diccionario."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "analyzed": self.analyzed,
            "metadata": self.metadata,
            "llm_analysis": self.llm_analysis,
            "geo_data": self.geo_data,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude
            } if self.latitude and self.longitude else None,
            "detections": [d.to_dict() for d in self.detections] if self.detections else []
        }

class FrameDetection(Base):
    """Modelo para almacenar detecciones de objetos en fotogramas de video."""
    
    __tablename__ = "frame_detections"
    
    id = Column(Integer, primary_key=True)
    frame_id = Column(Integer, ForeignKey("video_frames.id"))
    object_class = Column(String(100))
    confidence = Column(Float)
    bbox_x1 = Column(Integer)
    bbox_y1 = Column(Integer)
    bbox_x2 = Column(Integer)
    bbox_y2 = Column(Integer)
    
    # Relaciones
    frame = relationship("VideoFrame", back_populates="detections")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a un diccionario."""
        return {
            "id": self.id,
            "frame_id": self.frame_id,
            "object_class": self.object_class,
            "confidence": self.confidence,
            "bbox": [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2]
        }

class DBManager:
    """Gestor de base de datos para operaciones comunes."""
    
    def __init__(self):
        """Inicializa el gestor de base de datos."""
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Crea todas las tablas definidas en los modelos."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tablas de base de datos creadas correctamente")
        except Exception as e:
            logger.error(f"Error al crear tablas de base de datos: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """
        Obtiene una sesión de base de datos.
        
        Returns:
            Sesión de SQLAlchemy
        """
        return self.SessionLocal()
    
    def save_analysis(self, analysis_data: Dict[str, Any]) -> Analysis:
        """
        Guarda o actualiza un análisis de imagen.
        
        Args:
            analysis_data: Datos del análisis
            
        Returns:
            Objeto Analysis guardado
        """
        session = self.get_session()
        try:
            # Obtener ID de imagen
            image_id = analysis_data.get("image_id")
            if not image_id:
                raise ValueError("Se requiere image_id para guardar el análisis")
            
            # Buscar análisis existente o crear nuevo
            analysis = session.query(Analysis).filter_by(image_id=image_id).first()
            if not analysis:
                analysis = Analysis(image_id=image_id)
            
            # Actualizar campos básicos
            for key in ["filename", "file_path", "status"]:
                if key in analysis_data:
                    setattr(analysis, key, analysis_data[key])
            
            # Actualizar datos de análisis
            for key in ["metadata", "llm_analysis", "geo_data"]:
                if key in analysis_data:
                    setattr(analysis, key, analysis_data[key])
            
            # Actualizar coordenadas si están disponibles
            geo_data = analysis_data.get("geo_data", {})
            if geo_data:
                coordinates = geo_data.get("coordinates", {})
                if coordinates:
                    analysis.latitude = coordinates.get("latitude")
                    analysis.longitude = coordinates.get("longitude")
                
                analysis.country = geo_data.get("country")
                analysis.city = geo_data.get("city")
                analysis.confidence = geo_data.get("confidence")
            
            # Procesar detecciones si existen
            detections_data = analysis_data.get("detections", [])
            if detections_data:
                # Limpiar detecciones existentes
                for detection in analysis.detections:
                    session.delete(detection)
                
                # Crear nuevas detecciones
                for det_data in detections_data:
                    bbox = det_data.get("bbox", [0, 0, 0, 0])
                    detection = Detection(
                        object_class=det_data.get("class", "unknown"),
                        confidence=det_data.get("confidence", 0.0),
                        bbox_x1=bbox[0],
                        bbox_y1=bbox[1],
                        bbox_x2=bbox[2],
                        bbox_y2=bbox[3]
                    )
                    analysis.detections.append(detection)
            
            # Guardar cambios
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            
            logger.info(f"Análisis guardado para image_id: {image_id}")
            return analysis
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error al guardar análisis: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_analysis(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un análisis por ID de imagen.
        
        Args:
            image_id: ID de la imagen
            
        Returns:
            Datos del análisis o None si no existe
        """
        session = self.get_session()
        try:
            analysis = session.query(Analysis).filter_by(image_id=image_id).first()
            if not analysis:
                return None
            
            return analysis.to_dict()
            
        except Exception as e:
            logger.error(f"Error al obtener análisis: {str(e)}")
            return None
        finally:
            session.close()
    
    def list_analyses(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Lista análisis paginados.
        
        Args:
            limit: Límite de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            Lista de análisis
        """
        session = self.get_session()
        try:
            analyses = session.query(Analysis).order_by(
                Analysis.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return [a.to_dict() for a in analyses]
            
        except Exception as e:
            logger.error(f"Error al listar análisis: {str(e)}")
            return []
        finally:
            session.close()
    
    def delete_analysis(self, image_id: str) -> bool:
        """
        Elimina un análisis por ID de imagen.
        
        Args:
            image_id: ID de la imagen
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        session = self.get_session()
        try:
            analysis = session.query(Analysis).filter_by(image_id=image_id).first()
            if not analysis:
                return False
            
            session.delete(analysis)
            session.commit()
            
            logger.info(f"Análisis eliminado: {image_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error al eliminar análisis: {str(e)}")
            return False
        finally:
            session.close()
    
    def check_db_connection(self) -> bool:
        """
        Verifica la conexión a la base de datos.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Intentar conectar
            connection = self.engine.connect()
            connection.close()
            return True
        except Exception as e:
            logger.error(f"Error de conexión a la base de datos: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la base de datos.
        
        Returns:
            Diccionario con estadísticas
        """
        session = self.get_session()
        try:
            stats = {
                "analyses_count": session.query(Analysis).count(),
                "detections_count": session.query(Detection).count(),
                "video_analyses_count": session.query(VideoAnalysis).count(),
                "video_frames_count": session.query(VideoFrame).count(),
                "database_url": DB_URL.split("@")[-1] if "@" in DB_URL else DB_URL,
                "tables": [t for t in inspect(self.engine).get_table_names()]
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de la base de datos: {str(e)}")
            return {"error": str(e)}
        finally:
            session.close()

# Instancia global del gestor de base de datos
db_manager = DBManager()

# Crear tablas al importar el módulo
try:
    db_manager.create_tables()
except Exception as e:
    logger.error(f"Error al inicializar la base de datos: {str(e)}") 