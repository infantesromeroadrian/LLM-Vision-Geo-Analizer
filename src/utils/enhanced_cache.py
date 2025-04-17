"""
Sistema de caché avanzado con TTL y algoritmo LRU para Drone-OSINT-GeoSpy.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCache:
    """
    Implementación de caché avanzado con TTL (Time-To-Live) y algoritmo LRU (Least Recently Used).
    Thread-safe para entornos concurrentes.
    """
    
    def __init__(self, name: str, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Inicializa el caché con parámetros configurables.
        
        Args:
            name: Nombre identificativo del caché
            max_size: Tamaño máximo del caché (entradas)
            ttl_seconds: Tiempo de vida de las entradas en segundos
        """
        self.name = name
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self.creation_times: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.lock = threading.Lock()
        self.hit_count = 0
        self.miss_count = 0
        logger.info(f"EnhancedCache '{name}' inicializado: max_size={max_size}, ttl={ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché. Actualiza estadísticas y tiempo de acceso.
        
        Args:
            key: Clave a buscar
            
        Returns:
            Valor almacenado o None si no existe o está expirado
        """
        with self.lock:
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            # Verificar si ha expirado
            now = time.time()
            if now - self.creation_times[key] > self.ttl:
                self._remove_entry(key)
                self.miss_count += 1
                logger.debug(f"Cache '{self.name}': expirada clave '{key}'")
                return None
            
            # Actualizar tiempo de acceso
            self.access_times[key] = now
            self.hit_count += 1
            logger.debug(f"Cache '{self.name}': hit para clave '{key}'")
            return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        Almacena un valor en el caché.
        
        Args:
            key: Clave a almacenar
            value: Valor asociado a la clave
        """
        with self.lock:
            # Verificar si es necesario liberar espacio
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_entries()
            
            # Almacenar nueva entrada
            now = time.time()
            self.cache[key] = value
            self.access_times[key] = now
            self.creation_times[key] = now
            logger.debug(f"Cache '{self.name}': set para clave '{key}'")
    
    def _evict_entries(self) -> None:
        """
        Libera espacio en el caché según políticas de expiración y LRU.
        Primero elimina entradas expiradas, luego las menos usadas recientemente.
        """
        # Eliminar entradas expiradas primero
        now = time.time()
        expired_keys = [k for k in self.cache.keys() 
                        if now - self.creation_times[k] > self.ttl]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        # Si aún necesitamos espacio, usar LRU
        if len(self.cache) >= self.max_size:
            # Encontrar la entrada menos usada recientemente
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            self._remove_entry(oldest_key)
            logger.debug(f"Cache '{self.name}': LRU eviction para clave '{oldest_key}'")
    
    def _remove_entry(self, key: str) -> None:
        """
        Elimina una entrada del caché.
        
        Args:
            key: Clave a eliminar
        """
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.creation_times.pop(key, None)
    
    def clear(self) -> None:
        """Limpia completamente el caché."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.creation_times.clear()
            logger.info(f"Cache '{self.name}': limpiado completamente")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del rendimiento del caché.
        
        Returns:
            Diccionario con estadísticas (hits, misses, ratio, etc.)
        """
        with self.lock:
            total = self.hit_count + self.miss_count
            hit_ratio = self.hit_count / total if total > 0 else 0
            
            return {
                "name": self.name,
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
                "hits": self.hit_count,
                "misses": self.miss_count,
                "hit_ratio": hit_ratio,
                "entries": len(self.cache)
            }
    
    def cleanup_expired(self) -> int:
        """
        Elimina todas las entradas expiradas.
        
        Returns:
            Número de entradas eliminadas
        """
        with self.lock:
            now = time.time()
            expired_keys = [k for k in self.cache.keys() 
                           if now - self.creation_times[k] > self.ttl]
            
            for key in expired_keys:
                self._remove_entry(key)
            
            return len(expired_keys)
    
    def contains(self, key: str) -> bool:
        """
        Verifica si una clave existe en el caché y no ha expirado.
        
        Args:
            key: Clave a verificar
            
        Returns:
            True si la clave existe y no ha expirado
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            # Verificar si ha expirado
            now = time.time()
            if now - self.creation_times[key] > self.ttl:
                return False
            
            return True

class CacheManager:
    """
    Gestor centralizado para todos los cachés de la aplicación.
    Proporciona acceso unificado y estadísticas globales.
    """
    
    def __init__(self):
        """Inicializa el gestor de cachés."""
        self.caches: Dict[str, EnhancedCache] = {}
        self.cleanup_thread = None
        self.is_running = False
        self.lock = threading.Lock()
    
    def get_or_create_cache(self, name: str, max_size: int = 100, ttl_seconds: int = 3600) -> EnhancedCache:
        """
        Obtiene un caché existente o crea uno nuevo.
        
        Args:
            name: Nombre del caché
            max_size: Tamaño máximo del caché
            ttl_seconds: Tiempo de vida de las entradas
            
        Returns:
            Instancia de EnhancedCache
        """
        with self.lock:
            if name not in self.caches:
                self.caches[name] = EnhancedCache(name, max_size, ttl_seconds)
            return self.caches[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene estadísticas de todos los cachés.
        
        Returns:
            Diccionario con estadísticas por caché
        """
        stats = {}
        with self.lock:
            for name, cache in self.caches.items():
                stats[name] = cache.get_stats()
        return stats
    
    def start_cleanup_thread(self, interval_seconds: int = 300) -> None:
        """
        Inicia un hilo para limpieza periódica de entradas expiradas.
        
        Args:
            interval_seconds: Intervalo de limpieza en segundos
        """
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.cleanup_thread.start()
        logger.info(f"Iniciado hilo de limpieza de caché, intervalo: {interval_seconds}s")
    
    def stop_cleanup_thread(self) -> None:
        """Detiene el hilo de limpieza."""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=1.0)
            logger.info("Detenido hilo de limpieza de caché")
    
    def _cleanup_loop(self, interval_seconds: int) -> None:
        """
        Bucle de limpieza periódica.
        
        Args:
            interval_seconds: Intervalo de limpieza en segundos
        """
        while self.is_running:
            try:
                time.sleep(interval_seconds)
                
                with self.lock:
                    total_cleaned = 0
                    for name, cache in self.caches.items():
                        removed = cache.cleanup_expired()
                        total_cleaned += removed
                        
                if total_cleaned > 0:
                    logger.info(f"Limpieza de caché: eliminadas {total_cleaned} entradas expiradas")
                    
            except Exception as e:
                logger.error(f"Error en hilo de limpieza de caché: {str(e)}")
    
    def clear_all_caches(self) -> None:
        """Limpia todos los cachés."""
        with self.lock:
            for cache in self.caches.values():
                cache.clear()
            logger.info("Limpiados todos los cachés")

# Instancia global del gestor de cachés
cache_manager = CacheManager() 