#!/bin/bash
set -e

# Función para esperar a que el backend esté listo
wait_for_backend() {
    echo "Checking if backend is ready..."
    
    # Intentarlo hasta 30 veces (5 minutos con 10 segundos entre intentos)
    for i in {1..30}; do
        if curl -s http://backend:8000/api/session/health > /dev/null 2>&1; then
            echo "Backend is ready!"
            return 0
        else
            echo "Backend not ready yet (attempt $i/30). Waiting 10 seconds..."
            sleep 10
        fi
    done
    
    echo "ERROR: Backend did not become available after 5 minutes!"
    return 1
}

# Debug: Mostrar variables de entorno
echo "DEBUG: Current environment variables:"
echo "PYTHONPATH=$PYTHONPATH"
echo "API_URL=$API_URL"
echo "WAIT_FOR_BACKEND=$WAIT_FOR_BACKEND"
echo "OPENAI_API_KEY length:" ${#OPENAI_API_KEY}

# Comprobar si la clave API de OpenAI está configurada
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable is not set!"
    echo "Vision features will not work without an OpenAI API key."
fi

case "$1" in
    backend)
        echo "Starting backend server..."
        cd /app && python src/main.py
        ;;
    django_frontend)
        echo "Starting Django frontend server..."
        
        # Comprobar si necesitamos esperar al backend
        if [ "$WAIT_FOR_BACKEND" = "true" ] && [ -n "$API_URL" ]; then
            echo "Wait for backend is enabled. API_URL=$API_URL"
            wait_for_backend || echo "WARNING: Proceeding without confirmed backend connection!"
        else
            echo "No wait for backend requested or API_URL not set."
        fi
        
        # Aplicar migraciones de Django
        cd /app/src/django_frontend
        echo "Running Django migrations..."
        python manage.py makemigrations
        python manage.py migrate
        
        # Recopilar archivos estáticos
        echo "Collecting static files..."
        python manage.py collectstatic --noinput
        
        # Iniciar servidor Django
        echo "Starting Django server..."
        python manage.py runserver 0.0.0.0:8080
        ;;
    all)
        echo "Starting both backend and Django frontend..."
        cd /app && python src/main.py &
        BACKEND_PID=$!
        
        echo "Backend started with PID $BACKEND_PID"
        wait_for_backend
        
        echo "Starting Django frontend..."
        cd /app/src/django_frontend
        python manage.py makemigrations
        python manage.py migrate
        python manage.py collectstatic --noinput
        python manage.py runserver 0.0.0.0:8080
        ;;
    debug)
        echo "===== DEBUG MODE ====="
        echo "Current directory: $(pwd)"
        echo "Directory listing:"
        ls -la
        echo "Python environment:"
        python --version
        echo "Python path:"
        python -c "import sys; print(sys.path)"
        echo "Installed packages:"
        pip list
        echo "Testing imports:"
        python -c "
try:
    import openai
    print(f'OpenAI version: {openai.__version__}')
    from openai import OpenAI
    print('Successfully imported OpenAI client')
except Exception as e:
    print(f'Error importing OpenAI: {e}')
"
        echo "======================"
        ;;
    test-backend)
        echo "===== TESTING BACKEND INITIALIZATION ====="
        cd /app
        echo "Testing backend module imports..."
        python -c "
try:
    print('Importing backend modules...')
    if '/app' in '${PYTHONPATH}':
        print('Using Docker import paths')
        from models.vision_llm import VisionLLM
        from utils.metadata_extractor import MetadataExtractor
        from utils.geo_service import GeoService
    else:
        print('Using local import paths')
        from src.models.vision_llm import VisionLLM
        from src.utils.metadata_extractor import MetadataExtractor
        from src.utils.geo_service import GeoService
    
    print('All modules imported successfully!')
    
    print('Testing OpenAI client initialization...')
    import os
    api_key = os.environ.get('OPENAI_API_KEY', '')
    vision_llm = VisionLLM(api_key=api_key)
    print('VisionLLM initialized successfully')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
        ;;
    *)
        exec "$@"
        ;;
esac 