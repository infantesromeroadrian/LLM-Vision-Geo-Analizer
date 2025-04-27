FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DOCKER_CONTAINER=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for OpenEXIF and metadata extraction
    libexif-dev \
    libglib2.0-0 \
    # Required for OpenCV
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    # Required for healthchecks
    curl \
    dos2unix \
    # Cleanup
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Create and set work directory
WORKDIR /app

# Copy project files first
COPY . /app/

# Convert line endings for the entrypoint script
RUN dos2unix /app/docker-entrypoint.sh

# Install backend requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install Django frontend requirements if they exist
RUN if [ -f src/django_frontend/requirements.txt ]; then \
      pip install --no-cache-dir -r src/django_frontend/requirements.txt; \
    else \
      echo "Django requirements not found"; \
    fi

# Make sure the entrypoint script is executable
RUN chmod +x /app/docker-entrypoint.sh

# Create media directory for Django
RUN mkdir -p /app/src/django_frontend/media

# Set up volume for data persistence
VOLUME ["/app/data"]

# Expose ports - Backend and Django Frontend
EXPOSE 8000 8080

# Set entrypoint 
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command (can be overridden)
CMD ["all"] 