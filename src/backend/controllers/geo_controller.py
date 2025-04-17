from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos de datos para solicitudes
class MapRequest(BaseModel):
    latitude: float
    longitude: float
    zoom: int = 13

class GeocodeRequest(BaseModel):
    query: str
    limit: int = 5

class ReverseGeocodeRequest(BaseModel):
    latitude: float
    longitude: float

class StaticMapRequest(BaseModel):
    latitude: float
    longitude: float
    style: str = "satellite-streets-v12"
    width: int = 800
    height: int = 600
    zoom: int = 15

# Crear router para endpoints de geolocalización
router = APIRouter(prefix="/api", tags=["Geolocation"])

# Cache para resultados de geolocalización (se mejorará con EnhancedCache)
geocode_cache = {}

@router.post("/generate/map", response_model=Dict[str, Any])
async def generate_map(request: MapRequest):
    """
    Genera un mapa interactivo para las coordenadas especificadas.
    
    Args:
        request: Solicitud con latitud, longitud y nivel de zoom
        
    Returns:
        Diccionario con URL del mapa generado
    """
    try:
        # Implementar generación de mapa con servicio dedicado
        # Por ahora, devolvemos una respuesta simulada
        
        # Construir clave de caché
        cache_key = f"map_{request.latitude}_{request.longitude}_{request.zoom}"
        
        # Verificar caché
        if cache_key in geocode_cache:
            logger.info(f"Cache hit for map generation: {cache_key}")
            return geocode_cache[cache_key]
        
        # Simular generación de mapa (será implementado con servicio)
        map_data = {
            "success": True,
            "map_url": f"https://maps.example.com/?lat={request.latitude}&lng={request.longitude}&z={request.zoom}",
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "zoom": request.zoom
        }
        
        # Guardar en caché
        geocode_cache[cache_key] = map_data
        
        return map_data
        
    except Exception as e:
        logger.error(f"Error al generar mapa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar mapa: {str(e)}")

@router.post("/generate/interactive_map", response_model=Dict[str, Any])
async def generate_interactive_map(request: MapRequest):
    """
    Genera un mapa interactivo HTML para las coordenadas especificadas.
    
    Args:
        request: Solicitud con latitud, longitud y nivel de zoom
        
    Returns:
        Diccionario con HTML del mapa interactivo
    """
    try:
        # Construir clave de caché
        cache_key = f"interactive_map_{request.latitude}_{request.longitude}_{request.zoom}"
        
        # Verificar caché
        if cache_key in geocode_cache:
            logger.info(f"Cache hit for interactive map generation: {cache_key}")
            return geocode_cache[cache_key]
        
        # Importar GeoService
        try:
            from src.utils.geo_service import GeoService
        except ImportError:
            try:
                from utils.geo_service import GeoService
            except ImportError as e:
                logger.error(f"No se pudo importar GeoService: {str(e)}")
                # Fallback basic response if GeoService can't be imported
                return {
                    "success": False,
                    "error": "Service not available",
                    "map_html": f"""<div style="padding: 20px; background-color: #f8f9fa; border: 1px solid #ddd; text-align: center;">
                                  Map service not available.<br>Coordinates: {request.latitude}, {request.longitude}
                                  </div>""",
                    "coordinates": {
                        "latitude": request.latitude,
                        "longitude": request.longitude
                    },
                    "zoom": request.zoom
                }
        
        # Crear servicio de geolocalización
        geo_service = GeoService()
        
        # Verificar que el token de Mapbox esté disponible
        if not geo_service.mapbox_token:
            logger.warning("Mapbox API token not available")
            # Intentar usar el mapa básico si el token no está disponible
            basic_map = geo_service.generate_map(
                latitude=request.latitude,
                longitude=request.longitude,
                zoom=request.zoom
            )
            if basic_map:
                return {
                    "success": True,
                    "map_html": basic_map,
                    "map_type": "basic",
                    "coordinates": {
                        "latitude": request.latitude,
                        "longitude": request.longitude
                    },
                    "zoom": request.zoom
                }
        
        # Generar mapa interactivo
        map_html = geo_service.generate_interactive_map(
            latitude=request.latitude,
            longitude=request.longitude,
            zoom=request.zoom
        )
        
        # Si falla la generación, intentar usar el mapa básico
        if not map_html:
            logger.warning("Interactive map generation failed, trying basic map")
            map_html = geo_service.generate_map(
                latitude=request.latitude,
                longitude=request.longitude,
                zoom=request.zoom
            )
            if not map_html:
                # Si todo falla, devolver un mensaje formateado
                map_html = f"""<div style="padding: 20px; background-color: #f8f9fa; border: 1px solid #ddd; text-align: center;">
                            Map generation failed.<br>Coordinates: {request.latitude}, {request.longitude}
                            </div>"""
        
        # Preparar respuesta
        map_data = {
            "success": True,
            "map_html": map_html,
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "zoom": request.zoom
        }
        
        # Guardar en caché
        geocode_cache[cache_key] = map_data
        
        return map_data
        
    except Exception as e:
        logger.error(f"Error al generar mapa interactivo: {str(e)}")
        # Devolver un mensaje formateado en caso de error
        return {
            "success": False,
            "error": str(e),
            "map_html": f"""<div style="padding: 20px; background-color: #f8f9fa; border: 1px solid #ddd; text-align: center;">
                         Error generating map: {str(e)}<br>Coordinates: {request.latitude}, {request.longitude}
                         </div>""",
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "zoom": request.zoom
        }

@router.post("/geocode/forward", response_model=Dict[str, Any])
async def geocode_forward(request: GeocodeRequest):
    """
    Realiza geocodificación directa (dirección a coordenadas).
    
    Args:
        request: Solicitud con consulta de búsqueda y límite de resultados
        
    Returns:
        Diccionario con resultados de geocodificación
    """
    try:
        # Construir clave de caché
        cache_key = f"geocode_{request.query}_{request.limit}"
        
        # Verificar caché
        if cache_key in geocode_cache:
            logger.info(f"Cache hit for geocoding: {cache_key}")
            return geocode_cache[cache_key]
        
        # Simular geocodificación (será implementado con servicio)
        geocode_results = {
            "success": True,
            "query": request.query,
            "results": [
                {
                    "name": f"Resultado para {request.query}",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "address": f"Dirección de ejemplo para {request.query}",
                    "confidence": 0.95
                }
            ]
        }
        
        # Guardar en caché
        geocode_cache[cache_key] = geocode_results
        
        return geocode_results
        
    except Exception as e:
        logger.error(f"Error en geocodificación directa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en geocodificación: {str(e)}")

@router.post("/geocode/reverse", response_model=Dict[str, Any])
async def geocode_reverse(request: ReverseGeocodeRequest):
    """
    Realiza geocodificación inversa (coordenadas a dirección).
    
    Args:
        request: Solicitud con latitud y longitud
        
    Returns:
        Diccionario con resultados de geocodificación inversa
    """
    try:
        # Construir clave de caché
        cache_key = f"rev_geocode_{request.latitude}_{request.longitude}"
        
        # Verificar caché
        if cache_key in geocode_cache:
            logger.info(f"Cache hit for reverse geocoding: {cache_key}")
            return geocode_cache[cache_key]
        
        # Simular geocodificación inversa (será implementado con servicio)
        reverse_results = {
            "success": True,
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "address": {
                "formatted": f"Dirección en {request.latitude}, {request.longitude}",
                "country": "País de ejemplo",
                "city": "Ciudad de ejemplo",
                "street": "Calle de ejemplo"
            }
        }
        
        # Guardar en caché
        geocode_cache[cache_key] = reverse_results
        
        return reverse_results
        
    except Exception as e:
        logger.error(f"Error en geocodificación inversa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en geocodificación inversa: {str(e)}")

@router.post("/static-map", response_model=Dict[str, Any])
async def get_static_map(request: StaticMapRequest):
    """
    Genera un mapa estático para las coordenadas especificadas.
    
    Args:
        request: Solicitud con parámetros del mapa estático
        
    Returns:
        Diccionario con URL del mapa estático
    """
    try:
        # Construir clave de caché
        cache_key = f"static_map_{request.latitude}_{request.longitude}_{request.zoom}_{request.width}_{request.height}_{request.style}"
        
        # Verificar caché
        if cache_key in geocode_cache:
            logger.info(f"Cache hit for static map: {cache_key}")
            return geocode_cache[cache_key]
            
        # Simular generación de mapa estático (será implementado con servicio)
        map_data = {
            "success": True,
            "map_url": f"https://maps.example.com/static?lat={request.latitude}&lng={request.longitude}&z={request.zoom}&w={request.width}&h={request.height}&style={request.style}",
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "dimensions": {
                "width": request.width,
                "height": request.height
            },
            "style": request.style,
            "zoom": request.zoom
        }
        
        # Guardar en caché
        geocode_cache[cache_key] = map_data
        
        return map_data
        
    except Exception as e:
        logger.error(f"Error al generar mapa estático: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar mapa estático: {str(e)}") 