"""
Script de inicialización del sistema para Drone-OSINT-GeoSpy.
Verifica y configura directorios, dependencias y servicios necesarios.
"""

import os
import sys
import logging
import shutil
import json
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemInitializer:
    """
    Clase para inicializar el sistema y verificar que todos los componentes
    estén correctamente configurados.
    """
    
    # Directorios base necesarios
    REQUIRED_DIRS = [
        "data",
        "data/uploads",
        "data/frames",
        "data/results",
        "data/exports",
        "data/logs",
        "data/cache"
    ]
    
    def __init__(self):
        """Inicializa el verificador del sistema."""
        self.status = {
            "directories": {},
            "services": {},
            "database": False,
            "api_keys": {},
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "timestamp": datetime.now().isoformat()
        }
        logger.info("Iniciando verificación del sistema")
    
    def check_directories(self) -> Dict[str, bool]:
        """
        Verifica y crea los directorios necesarios.
        
        Returns:
            Diccionario con estado de los directorios
        """
        logger.info("Verificando directorios del sistema")
        for directory in self.REQUIRED_DIRS:
            try:
                os.makedirs(directory, exist_ok=True)
                self.status["directories"][directory] = True
                logger.info(f"Directorio verificado: {directory}")
            except Exception as e:
                self.status["directories"][directory] = False
                logger.error(f"Error al crear directorio {directory}: {str(e)}")
        
        return self.status["directories"]
    
    def check_api_keys(self) -> Dict[str, bool]:
        """
        Verifica las claves de API requeridas.
        
        Returns:
            Diccionario con estado de las claves API
        """
        logger.info("Verificando claves de API")
        
        # Lista de claves a verificar
        api_keys = {
            "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY"),
            "MAPBOX_API_KEY": os.environ.get("MAPBOX_API_KEY"),
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY")
        }
        
        for key, value in api_keys.items():
            self.status["api_keys"][key] = bool(value)
            if value:
                logger.info(f"Clave API encontrada: {key}")
            else:
                logger.warning(f"Clave API no encontrada: {key}")
        
        return self.status["api_keys"]
    
    def check_database(self) -> bool:
        """
        Verifica la conexión a la base de datos.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        logger.info("Verificando conexión a la base de datos")
        
        try:
            # Importar gestor de base de datos
            try:
                from src.models.database import db_manager
            except ImportError:
                from models.database import db_manager
            
            # Verificar conexión
            connection_ok = db_manager.check_db_connection()
            
            if connection_ok:
                logger.info("Conexión a la base de datos establecida correctamente")
                # Obtener estadísticas
                self.status["database_stats"] = db_manager.get_database_stats()
            else:
                logger.error("No se pudo conectar a la base de datos")
            
            self.status["database"] = connection_ok
            return connection_ok
            
        except Exception as e:
            logger.error(f"Error al verificar la base de datos: {str(e)}")
            self.status["database"] = False
            self.status["database_error"] = str(e)
            return False
    
    def check_services(self) -> Dict[str, bool]:
        """
        Verifica los servicios externos requeridos.
        
        Returns:
            Diccionario con estado de los servicios
        """
        logger.info("Verificando servicios externos")
        
        # Servicios a verificar
        services = {
            "vision_llm": False,
            "object_detector": False,
            "geo_service": False,
            "mapbox_service": False
        }
        
        # Verificar LLM
        try:
            try:
                from src.models.vision_llm import VisionLLM
            except ImportError:
                from models.vision_llm import VisionLLM
                
            # Verificar inicialización
            vision_llm = VisionLLM()
            services["vision_llm"] = True
            logger.info("Servicio VisionLLM inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar VisionLLM: {str(e)}")
            services["vision_llm_error"] = str(e)
        
        # Verificar detector de objetos
        try:
            try:
                from src.models.object_detector import ObjectDetector
            except ImportError:
                from models.object_detector import ObjectDetector
                
            # Verificar inicialización
            object_detector = ObjectDetector()
            services["object_detector"] = True
            logger.info("Servicio ObjectDetector inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar ObjectDetector: {str(e)}")
            services["object_detector_error"] = str(e)
        
        # Actualizar estado
        self.status["services"] = services
        return services
    
    def initialize_system(self) -> Dict[str, Any]:
        """
        Realiza todas las verificaciones e inicializaciones.
        
        Returns:
            Diccionario con el estado completo del sistema
        """
        # Verificar directorios
        self.check_directories()
        
        # Verificar claves API
        self.check_api_keys()
        
        # Verificar base de datos
        self.check_database()
        
        # Verificar servicios
        self.check_services()
        
        # Generar archivo de estado
        try:
            status_path = "data/system_status.json"
            with open(status_path, "w") as f:
                json.dump(self.status, f, indent=2)
            logger.info(f"Estado del sistema guardado en {status_path}")
        except Exception as e:
            logger.error(f"Error al guardar estado del sistema: {str(e)}")
        
        return self.status
    
    def clean_temp_files(self, max_age_days: int = 7) -> int:
        """
        Limpia archivos temporales antiguos.
        
        Args:
            max_age_days: Edad máxima en días para los archivos
            
        Returns:
            Número de archivos eliminados
        """
        logger.info(f"Limpiando archivos temporales con más de {max_age_days} días")
        
        # Directorios a limpiar
        temp_dirs = ["data/uploads", "data/frames", "data/results", "data/cache"]
        now = datetime.now()
        count = 0
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
                
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_age = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age_days = (now - file_age).days
                    
                    if age_days > max_age_days:
                        try:
                            os.remove(file_path)
                            count += 1
                            logger.debug(f"Eliminado archivo temporal: {file_path}")
                        except Exception as e:
                            logger.error(f"Error al eliminar archivo {file_path}: {str(e)}")
        
        logger.info(f"Limpieza completada: {count} archivos eliminados")
        return count

# Función principal para inicializar el sistema
def initialize_system() -> Dict[str, Any]:
    """
    Inicializa el sistema completo.
    
    Returns:
        Estado del sistema
    """
    initializer = SystemInitializer()
    return initializer.initialize_system()

# Ejecución directa
if __name__ == "__main__":
    # Inicializar sistema
    status = initialize_system()
    
    # Mostrar estado
    print(json.dumps(status, indent=2))
    
    # Verificar si hay errores críticos
    critical_error = False
    
    if not all(status["directories"].values()):
        print("\n❌ ERROR CRÍTICO: No se pudieron crear todos los directorios necesarios.")
        critical_error = True
    
    if not status["database"]:
        print("\n⚠️ ADVERTENCIA: No se pudo conectar a la base de datos.")
    
    if not any(status["api_keys"].values()):
        print("\n⚠️ ADVERTENCIA: No se encontraron claves de API configuradas.")
    
    # Salir con código de error si hay errores críticos
    if critical_error:
        sys.exit(1) 