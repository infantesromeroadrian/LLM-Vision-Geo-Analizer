/**
 * Drone OSINT GeoSpy - Advanced Mapbox Functions
 * 
 * Este módulo proporciona funcionalidades avanzadas de mapbox para
 * análisis geoespacial, seguimiento de drones y visualización de datos.
 */

// Namespace para nuestras funcionalidades
const DroneMapbox = {
    // Configuración
    config: {
        terrainSource: 'mapbox-dem',
        terrainExaggeration: 1.5,
        defaultMapStyle: 'mapbox://styles/mapbox/dark-v11',
        satelliteMapStyle: 'mapbox://styles/mapbox/satellite-streets-v12',
        dronePathColor: '#00e5ff',
        droneIconSize: 0.75,
        heatmapColors: [
            'interpolate', ['linear'], ['heatmap-density'],
            0, 'rgba(0,0,0,0)',
            0.2, '#0a4b91',
            0.4, '#1a6ed8',
            0.6, '#00b8d4',
            0.8, '#00e5ff',
            1, '#ffffff'
        ]
    },
    
    /**
     * Inicializa un mapa 3D con terreno
     * @param {string} containerId - ID del contenedor HTML del mapa
     * @param {Array} centerCoords - Coordenadas [lng, lat] iniciales
     * @param {number} zoom - Nivel de zoom inicial
     * @param {string} style - Estilo del mapa (opcional)
     * @returns {Object} Instancia del mapa
     */
    initMap3D: function(containerId, centerCoords, zoom, style) {
        // Comprobamos si mapboxgl está disponible
        if (!mapboxgl) {
            console.error('Mapbox GL JS no está cargado');
            return null;
        }
        
        // Inicializamos el mapa
        const map = new mapboxgl.Map({
            container: containerId,
            style: style || this.config.defaultMapStyle,
            center: centerCoords,
            zoom: zoom || 13,
            pitch: 60, // Ángulo para vista 3D
            bearing: 0,
            antialias: true
        });
        
        // Añadimos controles
        map.addControl(new mapboxgl.NavigationControl());
        map.addControl(new mapboxgl.FullscreenControl());
        map.addControl(new mapboxgl.GeolocateControl({
            positionOptions: { enableHighAccuracy: true },
            trackUserLocation: true
        }));
        
        // Cuando el mapa carga, añadimos fuente de terreno 3D
        map.on('load', () => {
            map.addSource('mapbox-dem', {
                'type': 'raster-dem',
                'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
                'tileSize': 512,
                'maxzoom': 14
            });
            
            // Activamos terreno 3D
            map.setTerrain({ 
                'source': this.config.terrainSource, 
                'exaggeration': this.config.terrainExaggeration 
            });
            
            // Añadimos niebla atmosférica
            map.setFog({
                'color': 'rgb(12, 24, 36)',
                'high-color': 'rgb(36, 92, 223)',
                'horizon-blend': 0.1,
                'space-color': 'rgb(11, 11, 25)',
                'star-intensity': 0.35
            });
        });
        
        return map;
    },
    
    /**
     * Cambia el estilo del mapa (incluidos estilos nocturnos y satélite)
     * @param {Object} map - Instancia del mapa
     * @param {string} styleType - Tipo de estilo ('default', 'satellite', 'night', 'terrain')
     */
    changeMapStyle: function(map, styleType) {
        let styleUrl;
        
        switch(styleType) {
            case 'satellite':
                styleUrl = this.config.satelliteMapStyle;
                break;
            case 'night':
                styleUrl = 'mapbox://styles/mapbox/navigation-night-v1';
                break;
            case 'terrain':
                styleUrl = 'mapbox://styles/mapbox/outdoors-v12';
                break;
            default:
                styleUrl = this.config.defaultMapStyle;
        }
        
        map.setStyle(styleUrl);
        
        // Volvemos a configurar el terreno después del cambio de estilo
        map.once('styledata', () => {
            if (!map.getSource('mapbox-dem')) {
                map.addSource('mapbox-dem', {
                    'type': 'raster-dem',
                    'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
                    'tileSize': 512,
                    'maxzoom': 14
                });
                
                map.setTerrain({ 
                    'source': this.config.terrainSource, 
                    'exaggeration': this.config.terrainExaggeration 
                });
            }
        });
    },
    
    /**
     * Visualiza y anima la trayectoria de un dron
     * @param {Object} map - Instancia del mapa
     * @param {Object} pathData - Datos GeoJSON con la trayectoria
     * @param {string} layerId - ID para la capa del mapa
     * @param {boolean} animate - Si se debe animar la trayectoria
     */
    addDronePath: function(map, pathData, layerId = 'drone-path', animate = true) {
        // Esperar a que el mapa termine de cargar
        if (!map.loaded()) {
            map.on('load', () => this.addDronePath(map, pathData, layerId, animate));
            return;
        }
        
        // Añadir fuente de datos si no existe
        if (!map.getSource(layerId + '-source')) {
            map.addSource(layerId + '-source', {
                'type': 'geojson',
                'data': pathData
            });
        }
        
        // Añadir capa de línea para la trayectoria
        if (!map.getLayer(layerId)) {
            map.addLayer({
                'id': layerId,
                'type': 'line',
                'source': layerId + '-source',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': this.config.dronePathColor,
                    'line-width': 2,
                    'line-dasharray': [2, 1]
                }
            });
        }
        
        // Añadir dron animado si se solicita
        if (animate && pathData.features && pathData.features.length > 0) {
            // Crear punto para representar el dron
            const dronePoint = {
                'type': 'FeatureCollection',
                'features': [{
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'Point',
                        'coordinates': pathData.features[0].geometry.coordinates[0]
                    }
                }]
            };
            
            // Añadir fuente para el dron
            const droneSourceId = layerId + '-drone-source';
            if (!map.getSource(droneSourceId)) {
                map.addSource(droneSourceId, {
                    'type': 'geojson',
                    'data': dronePoint
                });
            }
            
            // Añadir capa para el dron
            const droneLayerId = layerId + '-drone';
            if (!map.getLayer(droneLayerId)) {
                map.addLayer({
                    'id': droneLayerId,
                    'type': 'symbol',
                    'source': droneSourceId,
                    'layout': {
                        'icon-image': 'airport', // Símbolo de avión o dron
                        'icon-size': this.config.droneIconSize,
                        'icon-allow-overlap': true,
                        'icon-rotate': ['get', 'bearing'],
                        'icon-rotation-alignment': 'map'
                    }
                });
            }
            
            // Animar el dron a lo largo de la trayectoria
            this.animateDrone(map, pathData, droneSourceId);
        }
    },
    
    /**
     * Anima un dron a lo largo de una trayectoria
     * @param {Object} map - Instancia del mapa
     * @param {Object} pathData - Datos GeoJSON con la trayectoria
     * @param {string} droneSourceId - ID de la fuente del dron
     */
    animateDrone: function(map, pathData, droneSourceId) {
        if (!pathData.features || !pathData.features[0] || 
            !pathData.features[0].geometry || !pathData.features[0].geometry.coordinates) {
            console.error('Formato de datos de trayectoria incorrecto');
            return;
        }
        
        const coordinates = pathData.features[0].geometry.coordinates;
        let startTime = performance.now();
        const animationDuration = coordinates.length * 1000; // 1 segundo por punto
        
        const animateFrame = (timestamp) => {
            // Calcular el progreso de la animación
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / animationDuration, 1);
            
            // Calcular el índice actual
            const pointIndex = Math.min(
                Math.floor(progress * coordinates.length),
                coordinates.length - 1
            );
            
            // Actualizar posición del dron
            const currentCoord = coordinates[pointIndex];
            const nextCoord = pointIndex < coordinates.length - 1 ? 
                            coordinates[pointIndex + 1] : coordinates[pointIndex];
            
            // Calcular rumbo del dron
            const bearing = this.calculateBearing(currentCoord, nextCoord);
            
            // Actualizar la fuente con la nueva posición
            map.getSource(droneSourceId).setData({
                'type': 'FeatureCollection',
                'features': [{
                    'type': 'Feature',
                    'properties': {
                        'bearing': bearing
                    },
                    'geometry': {
                        'type': 'Point',
                        'coordinates': currentCoord
                    }
                }]
            });
            
            // Seguir animando si no hemos terminado
            if (progress < 1) {
                requestAnimationFrame(animateFrame);
            }
        };
        
        // Iniciar animación
        requestAnimationFrame(animateFrame);
    },
    
    /**
     * Calcula el rumbo entre dos coordenadas
     * @param {Array} start - Coordenadas de inicio [lng, lat]
     * @param {Array} end - Coordenadas de fin [lng, lat]
     * @returns {number} Rumbo en grados
     */
    calculateBearing: function(start, end) {
        const startLat = this.toRadians(start[1]);
        const startLng = this.toRadians(start[0]);
        const endLat = this.toRadians(end[1]);
        const endLng = this.toRadians(end[0]);
        
        const y = Math.sin(endLng - startLng) * Math.cos(endLat);
        const x = Math.cos(startLat) * Math.sin(endLat) -
                Math.sin(startLat) * Math.cos(endLat) * Math.cos(endLng - startLng);
        
        let bearing = Math.atan2(y, x);
        bearing = this.toDegrees(bearing);
        
        return (bearing + 360) % 360;
    },
    
    /**
     * Convierte grados a radianes
     * @param {number} degrees - Valor en grados
     * @returns {number} Valor en radianes
     */
    toRadians: function(degrees) {
        return degrees * Math.PI / 180;
    },
    
    /**
     * Convierte radianes a grados
     * @param {number} radians - Valor en radianes
     * @returns {number} Valor en grados
     */
    toDegrees: function(radians) {
        return radians * 180 / Math.PI;
    },
    
    /**
     * Añade un mapa de calor de actividad
     * @param {Object} map - Instancia del mapa
     * @param {Object} heatmapData - Datos GeoJSON con puntos de actividad
     * @param {string} layerId - ID para la capa del mapa
     */
    addHeatmap: function(map, heatmapData, layerId = 'activity-heat') {
        // Esperar a que el mapa termine de cargar
        if (!map.loaded()) {
            map.on('load', () => this.addHeatmap(map, heatmapData, layerId));
            return;
        }
        
        // Añadir fuente de datos
        if (!map.getSource(layerId + '-source')) {
            map.addSource(layerId + '-source', {
                'type': 'geojson',
                'data': heatmapData
            });
        }
        
        // Añadir capa de mapa de calor
        if (!map.getLayer(layerId)) {
            map.addLayer({
                'id': layerId,
                'type': 'heatmap',
                'source': layerId + '-source',
                'paint': {
                    'heatmap-weight': ['get', 'weight'],
                    'heatmap-intensity': 0.8,
                    'heatmap-color': this.config.heatmapColors,
                    'heatmap-radius': 15,
                    'heatmap-opacity': 0.75
                }
            });
        }
    },
    
    /**
     * Crea y gestiona geocercas (geofences)
     * @param {Object} map - Instancia del mapa
     * @param {string} containerId - ID del contenedor HTML del mapa
     */
    setupGeofencing: function(map, containerId) {
        // Esperar a que el mapa termine de cargar
        if (!map.loaded()) {
            map.on('load', () => this.setupGeofencing(map, containerId));
            return;
        }
        
        // Comprobar si Draw está disponible
        if (!MapboxDraw) {
            console.error('MapboxDraw no está disponible. Incluye esta librería en tu HTML.');
            console.info('Añade: <script src="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-draw/v1.4.0/mapbox-gl-draw.js"></script>');
            return;
        }
        
        // Crear instancia de Draw
        const draw = new MapboxDraw({
            displayControlsDefault: false,
            controls: {
                polygon: true,
                trash: true
            },
            styles: [
                // Estilos personalizados para las geocercas
                {
                    'id': 'gl-draw-polygon-fill',
                    'type': 'fill',
                    'filter': ['all', ['==', '$type', 'Polygon']],
                    'paint': {
                        'fill-color': '#00b8d4',
                        'fill-outline-color': '#00e5ff',
                        'fill-opacity': 0.1
                    }
                },
                {
                    'id': 'gl-draw-polygon-stroke-active',
                    'type': 'line',
                    'filter': ['all', ['==', '$type', 'Polygon']],
                    'paint': {
                        'line-color': '#00e5ff',
                        'line-width': 2,
                        'line-dasharray': [2, 1]
                    }
                },
                {
                    'id': 'gl-draw-point-active',
                    'type': 'circle',
                    'filter': ['all', ['==', '$type', 'Point'], ['!=', 'meta', 'midpoint']],
                    'paint': {
                        'circle-radius': 5,
                        'circle-color': '#00e5ff'
                    }
                }
            ]
        });
        
        // Añadir el control de dibujo al mapa
        map.addControl(draw);
        
        // Configurar el evento para cuando se crea/actualiza una geocerca
        map.on('draw.create', () => this.updateGeofenceInfo(draw));
        map.on('draw.update', () => this.updateGeofenceInfo(draw));
        map.on('draw.delete', () => this.updateGeofenceInfo(draw));
        
        // Crear elemento para mostrar información
        this.createGeofenceInfoPanel(containerId);
        
        return draw;
    },
    
    /**
     * Actualiza la información de las geocercas
     * @param {Object} draw - Instancia de MapboxDraw
     */
    updateGeofenceInfo: function(draw) {
        const features = draw.getAll();
        const geofenceInfo = document.getElementById('geofence-info');
        
        if (geofenceInfo) {
            // Mostrar el número de geocercas
            geofenceInfo.innerHTML = `<div class="geofence-count">Geocercas activas: ${features.features.length}</div>`;
            
            // Mostrar información de cada geocerca
            features.features.forEach((feature, index) => {
                // Calcular área aproximada en km²
                const area = turf.area(feature) / 1000000;
                
                // Añadir información al panel
                geofenceInfo.innerHTML += `
                    <div class="geofence-item">
                        <div class="geofence-title">Zona ${index + 1}</div>
                        <div class="geofence-area">Área: ${area.toFixed(2)} km²</div>
                    </div>
                `;
            });
        }
    },
    
    /**
     * Crea un panel de información para las geocercas
     * @param {string} mapContainerId - ID del contenedor del mapa
     */
    createGeofenceInfoPanel: function(mapContainerId) {
        const mapContainer = document.getElementById(mapContainerId);
        
        if (mapContainer) {
            // Crear panel si no existe
            if (!document.getElementById('geofence-info')) {
                const panel = document.createElement('div');
                panel.id = 'geofence-info';
                panel.className = 'geofence-info-panel';
                panel.innerHTML = '<div class="geofence-count">Geocercas activas: 0</div>';
                
                // Añadir estilos inline para el panel
                panel.style.position = 'absolute';
                panel.style.top = '10px';
                panel.style.right = '10px';
                panel.style.width = '250px';
                panel.style.padding = '10px';
                panel.style.backgroundColor = 'rgba(5, 8, 15, 0.8)';
                panel.style.border = '1px solid #00b8d4';
                panel.style.borderRadius = '3px';
                panel.style.color = '#e0f7fa';
                panel.style.fontFamily = '"Roboto Mono", monospace';
                panel.style.fontSize = '12px';
                panel.style.zIndex = '1';
                panel.style.boxShadow = '0 0 10px rgba(0, 229, 255, 0.3)';
                
                mapContainer.appendChild(panel);
            }
        }
    },
    
    /**
     * Comprueba si un punto está dentro de alguna geocerca
     * @param {Object} draw - Instancia de MapboxDraw
     * @param {Array} point - Coordenadas [lng, lat]
     * @returns {boolean} True si está dentro de alguna geocerca
     */
    isPointInGeofence: function(draw, point) {
        const features = draw.getAll();
        const pt = turf.point(point);
        
        for (let i = 0; i < features.features.length; i++) {
            const poly = features.features[i];
            if (turf.booleanPointInPolygon(pt, poly)) {
                return true;
            }
        }
        
        return false;
    },
    
    /**
     * Añade una capa de visibilidad (viewshed) desde un punto
     * @param {Object} map - Instancia del mapa
     * @param {Array} point - Coordenadas [lng, lat]
     * @param {number} radius - Radio en metros
     * @param {string} layerId - ID para la capa
     */
    addViewshed: function(map, point, radius = 1000, layerId = 'viewshed') {
        // Esta es una versión simplificada. En producción, sería necesario
        // utilizar un servicio de análisis espacial o implementar un algoritmo
        // de viewshed que tenga en cuenta la elevación.
        
        // Crear un círculo para representar el área visible
        const circle = turf.circle(point, radius / 1000, {
            steps: 64,
            units: 'kilometers'
        });
        
        // Esperar a que el mapa termine de cargar
        if (!map.loaded()) {
            map.on('load', () => this.addViewshed(map, point, radius, layerId));
            return;
        }
        
        // Añadir fuente
        if (!map.getSource(layerId + '-source')) {
            map.addSource(layerId + '-source', {
                'type': 'geojson',
                'data': circle
            });
        } else {
            map.getSource(layerId + '-source').setData(circle);
        }
        
        // Añadir capa si no existe
        if (!map.getLayer(layerId)) {
            map.addLayer({
                'id': layerId,
                'type': 'fill',
                'source': layerId + '-source',
                'paint': {
                    'fill-color': '#00e5ff',
                    'fill-opacity': 0.2,
                    'fill-outline-color': '#00b8d4'
                }
            });
        }
    }
};

// Exportar para uso en otros módulos
if (typeof module !== 'undefined') {
    module.exports = DroneMapbox;
} 