"""
Módulo para optimización de procesamiento de imágenes en Drone-OSINT-GeoSpy.
Proporciona funciones para escalar, comprimir y preprocesar imágenes de forma eficiente.
"""

import os
import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple, Dict, Any, Optional, Union
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageOptimizer:
    """
    Clase para optimizar imágenes antes del procesamiento por modelos AI.
    Proporciona métodos para escalar, comprimir y preprocesar imágenes.
    """
    
    def __init__(self, 
                 max_dimension: int = 1920, 
                 quality: int = 90,
                 auto_enhance: bool = True):
        """
        Inicializa el optimizador de imágenes.
        
        Args:
            max_dimension: Dimensión máxima de la imagen (ancho o alto)
            quality: Calidad de compresión JPEG (1-100)
            auto_enhance: Aplicar mejoras automáticas de contraste/brillo
        """
        self.max_dimension = max_dimension
        self.quality = quality
        self.auto_enhance = auto_enhance
        logger.info(f"ImageOptimizer inicializado: max_dimension={max_dimension}, quality={quality}")
    
    def process_image(self, 
                      image_path: str, 
                      output_path: Optional[str] = None,
                      resize: bool = True) -> Dict[str, Any]:
        """
        Procesa una imagen para optimizarla para análisis.
        
        Args:
            image_path: Ruta de la imagen de entrada
            output_path: Ruta para guardar la imagen optimizada (None = no guardar)
            resize: Aplicar redimensionamiento adaptativo
            
        Returns:
            Diccionario con información de la optimización
        """
        start_time = time.time()
        
        try:
            # Verificar archivo
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"No se encuentra la imagen: {image_path}")
            
            # Obtener tamaño original del archivo
            original_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
            
            # Cargar imagen con OpenCV
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"No se pudo cargar la imagen: {image_path}")
            
            # Obtener dimensiones originales
            original_height, original_width = img.shape[:2]
            
            # Determinar si se necesita redimensionar
            scaling_factor = 1.0
            if resize:
                if original_size > 10:  # Imágenes muy grandes (>10MB)
                    # Escala más agresiva para archivos muy grandes
                    scaling_factor = min(
                        self.max_dimension / original_width,
                        self.max_dimension / original_height,
                        0.5  # Máximo 50% de reducción en casos extremos
                    )
                elif max(original_height, original_width) > self.max_dimension:
                    # Escala estándar para dimensiones grandes
                    scaling_factor = min(
                        self.max_dimension / original_width,
                        self.max_dimension / original_height
                    )
            
            # Aplicar redimensionamiento si es necesario
            if scaling_factor < 1.0:
                new_width = int(original_width * scaling_factor)
                new_height = int(original_height * scaling_factor)
                img = cv2.resize(
                    img, 
                    (new_width, new_height), 
                    interpolation=cv2.INTER_AREA
                )
                logger.info(f"Imagen redimensionada: {original_width}x{original_height} -> {new_width}x{new_height}")
            else:
                new_width, new_height = original_width, original_height
            
            # Aplicar mejoras automáticas si está habilitado
            if self.auto_enhance:
                img = self._enhance_image(img)
            
            # Guardar imagen optimizada si se proporciona ruta
            if output_path:
                # Asegurar directorio de salida
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Guardar con la calidad especificada
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
                cv2.imwrite(output_path, img, encode_params)
                
                # Verificar tamaño del archivo resultante
                new_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                size_reduction = (1 - new_size / original_size) * 100 if original_size > 0 else 0
                
                logger.info(f"Imagen optimizada guardada: {output_path}")
                logger.info(f"Reducción de tamaño: {original_size:.2f}MB -> {new_size:.2f}MB ({size_reduction:.1f}%)")
            
            # Calcular tiempo de procesamiento
            process_time = time.time() - start_time
            
            # Devolver información del procesamiento
            return {
                "success": True,
                "original_path": image_path,
                "output_path": output_path,
                "original_dimensions": (original_width, original_height),
                "new_dimensions": (new_width, new_height),
                "original_size_mb": original_size,
                "scaling_factor": scaling_factor,
                "process_time_seconds": process_time,
                "enhanced": self.auto_enhance
            }
            
        except Exception as e:
            logger.error(f"Error al optimizar imagen: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_path": image_path
            }
    
    def _enhance_image(self, img: np.ndarray) -> np.ndarray:
        """
        Aplica mejoras automáticas a la imagen para aumentar la visibilidad.
        
        Args:
            img: Array de imagen OpenCV
            
        Returns:
            Imagen mejorada
        """
        try:
            # Convertir a escala de grises para análisis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calcular histograma
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # Determinar si la imagen es oscura o tiene bajo contraste
            is_dark = np.mean(gray) < 100
            low_contrast = np.std(gray) < 30
            
            # Imagen original para comparación
            enhanced = img.copy()
            
            # Aplicar mejoras según características
            if is_dark:
                # Aumentar brillo
                hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                
                # Incrementar valor (brillo)
                limit = 255 - 30
                v[v < limit] = v[v < limit] + 30
                
                hsv = cv2.merge((h, s, v))
                enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                
                logger.debug("Aplicada mejora de brillo a imagen oscura")
            
            if low_contrast:
                # Aplicar ecualización de histograma adaptativa
                lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                
                # Combinar canales nuevamente
                lab = cv2.merge((cl, a, b))
                enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                
                logger.debug("Aplicada ecualización de contraste adaptativa")
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error en _enhance_image: {str(e)}")
            return img  # Devolver imagen original en caso de error
    
    @staticmethod
    def estimate_memory_usage(height: int, width: int, channels: int = 3) -> float:
        """
        Estima el uso de memoria para procesar una imagen de las dimensiones dadas.
        
        Args:
            height: Altura de la imagen en píxeles
            width: Ancho de la imagen en píxeles
            channels: Número de canales (3 para RGB, 4 para RGBA)
            
        Returns:
            Uso estimado de memoria en MB
        """
        # Cada píxel ocupa 1 byte por canal
        bytes_per_pixel = channels
        
        # Memoria cruda para la imagen
        raw_size = height * width * bytes_per_pixel
        
        # OpenCV y otras bibliotecas pueden necesitar copias intermedias
        # Factor de multiplicación estimado: 4x para operaciones como redimensionamiento
        estimated_size = raw_size * 4
        
        # Convertir a MB
        return estimated_size / (1024 * 1024)
    
    def get_optimal_dimensions(self, 
                              width: int, 
                              height: int, 
                              file_size_mb: float) -> Tuple[int, int]:
        """
        Calcula las dimensiones óptimas para una imagen basándose en su tamaño.
        
        Args:
            width: Ancho original en píxeles
            height: Alto original en píxeles
            file_size_mb: Tamaño del archivo en MB
            
        Returns:
            Tupla con (nuevo_ancho, nuevo_alto)
        """
        # Dimensión máxima normal
        max_dim = self.max_dimension
        
        # Ajustar para archivos extremadamente grandes
        if file_size_mb > 20:
            max_dim = min(1280, max_dim)  # Más restrictivo para archivos muy grandes
        elif file_size_mb > 10:
            max_dim = min(1600, max_dim)
        
        # Calcular relación de aspecto
        aspect_ratio = width / height
        
        # Determinar nuevas dimensiones respetando la relación de aspecto
        if width > height:
            new_width = min(width, max_dim)
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = min(height, max_dim)
            new_width = int(new_height * aspect_ratio)
        
        return new_width, new_height 