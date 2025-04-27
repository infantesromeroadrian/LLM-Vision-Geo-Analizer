from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import requests
import json
import os
import uuid
import base64
from datetime import datetime
from .models import DroneImage, AnalysisResult, ChatMessage
import io
from PIL import Image
import hashlib

# API URL from settings
API_URL = settings.API_URL
MAPBOX_TOKEN = settings.MAPBOX_API_KEY

def index(request):
    """Home page view"""
    # Generate session ID if not present
    if 'session_id' not in request.session:
        request.session['session_id'] = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
    
    context = {
        'title': 'DRONE OSINT GEOSPY',
        'session_id': request.session['session_id'],
        'current_time': datetime.now().strftime("%H:%M:%S"),
    }
    return render(request, 'osint_geospy/index.html', context)

def image_analysis(request):
    """Image analysis view"""
    # Get recent images for display
    recent_images = DroneImage.objects.all().order_by('-uploaded_at')[:5]
    
    context = {
        'title': 'Image Analysis',
        'recent_images': recent_images,
        'mapbox_token': MAPBOX_TOKEN,
    }
    return render(request, 'osint_geospy/image_analysis.html', context)

@csrf_exempt
def analyze_image(request):
    """Handle image upload and analysis"""
    if request.method == 'POST':
        if 'image' in request.FILES:
            # Get uploaded image
            uploaded_file = request.FILES['image']
            
            # Save image to model
            drone_image = DroneImage(
                title=uploaded_file.name,
                image=uploaded_file
            )
            drone_image.save()
            
            # Call backend API to upload image
            try:
                image_data = open(drone_image.image.path, 'rb').read()
                files = {"file": (uploaded_file.name, image_data, "image/jpeg")}
                response = requests.post(f"{API_URL}/api/upload/image", files=files)
                
                if response.status_code == 200:
                    upload_data = response.json()
                    backend_image_id = upload_data.get("image_id")
                    
                    # Save the backend image ID to our model
                    drone_image.backend_image_id = backend_image_id
                    drone_image.save()
                    
                    # Analyze the image using backend
                    analysis_response = requests.post(f"{API_URL}/api/analyze/image/{backend_image_id}")
                    
                    if analysis_response.status_code == 200:
                        analysis_data = analysis_response.json()
                        
                        # Extract data with error handling
                        try:
                            # LLM Analysis
                            llm_analysis = analysis_data.get('llm_analysis', {})
                            if isinstance(llm_analysis, str):
                                description = llm_analysis
                                confidence = 'medium'
                            else:
                                description = llm_analysis.get('description', 'No description available')
                                confidence = llm_analysis.get('confidence', 'low')
                            
                            # Geo Data
                            geo_data = analysis_data.get('geo_data', {})
                            if isinstance(geo_data, str):
                                try:
                                    geo_data = json.loads(geo_data)
                                except json.JSONDecodeError:
                                    geo_data = {'text_analysis': geo_data}
                            
                            # Extract location data
                            country = geo_data.get('country', 'Unknown')
                            city = geo_data.get('city', 'Unknown')
                            neighborhood = geo_data.get('neighborhood', 'Unknown')
                            street = geo_data.get('street', 'Unknown')
                            coordinates = geo_data.get('coordinates', {})
                            lat = coordinates.get('latitude', 0)
                            lon = coordinates.get('longitude', 0)
                            features = geo_data.get('architectural_features', [])
                            landscape_features = geo_data.get('landscape_features', [])
                            
                            # Metadata
                            metadata = analysis_data.get('metadata', {})
                            camera_info = metadata.get('camera_info', {})
                            make = camera_info.get('make', 'Unknown')
                            model = camera_info.get('model', 'Unknown')
                            
                            # Update DroneImage model with metadata
                            drone_image.latitude = float(lat) if lat else None
                            drone_image.longitude = float(lon) if lon else None
                            drone_image.camera_make = make
                            drone_image.camera_model = model
                            drone_image.analyzed = True
                            drone_image.analysis_result = analysis_data
                            drone_image.save()
                            
                            # Create AnalysisResult object
                            analysis_result = AnalysisResult(
                                drone_image=drone_image,
                                country=country,
                                city=city,
                                street=street,
                                neighborhood=neighborhood,
                                description=description,
                                confidence=confidence,
                                architectural_features=features,
                                landscape_features=landscape_features
                            )
                            analysis_result.save()
                            
                            # Store the backend image ID in session
                            request.session['current_image_id'] = str(drone_image.image_id)
                            
                            return redirect('osint_geospy:image_analysis')
                            
                        except Exception as e:
                            messages.error(request, f"Error processing analysis: {str(e)}")
                    else:
                        messages.error(request, f"Error analyzing image: {analysis_response.text}")
                else:
                    messages.error(request, f"Error uploading to backend: {response.text}")
            
            except Exception as e:
                messages.error(request, f"Error communicating with backend: {str(e)}")
            
            return redirect('osint_geospy:image_analysis')
    
    return redirect('osint_geospy:image_analysis')

def drone_stream(request):
    """Drone stream view"""
    context = {
        'title': 'Drone Stream',
        'is_streaming': False,
        'mapbox_token': MAPBOX_TOKEN,
    }
    return render(request, 'osint_geospy/drone_stream.html', context)

def interrogation(request):
    """Chat interface for interrogating about images"""
    # Get chat history from session ID
    session_id = request.session.get('session_id', 'default_session')
    
    # Get chat messages for this session
    chat_messages = ChatMessage.objects.filter(session_id=session_id).order_by('timestamp')
    
    # Get current image if available
    current_image_id = request.session.get('current_image_id')
    current_image = None
    if current_image_id:
        try:
            current_image = DroneImage.objects.get(image_id=current_image_id)
        except DroneImage.DoesNotExist:
            pass
    
    context = {
        'title': 'Interrogation',
        'chat_messages': chat_messages,
        'current_image': current_image,
    }
    return render(request, 'osint_geospy/interrogation.html', context)

def search_location(request):
    """Search location and display on map"""
    if request.method == 'POST':
        location_query = request.POST.get('location_search', '')
        
        if location_query:
            try:
                # Call geocoding API
                geocode_response = requests.post(
                    f"{API_URL}/api/geocode/forward",
                    json={"query": location_query, "limit": 5}
                )
                
                if geocode_response.status_code == 200:
                    results = geocode_response.json().get("results", [])
                    
                    # Store results in session
                    request.session['location_results'] = results
                    
                    return redirect('osint_geospy:image_analysis')
                else:
                    messages.error(request, f"Error searching location: {geocode_response.text}")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    
    return redirect('osint_geospy:image_analysis')

@csrf_exempt
def chat_with_image(request):
    """API endpoint to chat with the image using Gemini"""
    if request.method == 'POST':
        try:
            # Get request data
            data = json.loads(request.body)
            user_message = data.get('message', '')
            image_id = data.get('image_id', '')
            
            # Validate inputs
            if not user_message or not image_id:
                return JsonResponse({'error': 'Message and image_id are required'}, status=400)
            
            # Get the image
            try:
                image = DroneImage.objects.get(image_id=image_id)
                
                # Check if we have a backend image ID
                if not image.backend_image_id:
                    return JsonResponse({'error': 'Esta imagen no tiene un ID de backend. Intenta analizarla nuevamente.'}, status=400)
                
                backend_image_id = image.backend_image_id
            except DroneImage.DoesNotExist:
                return JsonResponse({'error': 'Image not found'}, status=404)
                
            # Get session ID
            session_id = request.session.get('session_id', 'default_session')
            
            # Create new user message in database
            user_chat_message = ChatMessage.objects.create(
                role='user',
                content=user_message,
                session_id=session_id,
                related_image=image
            )
            
            # Call the backend API to get AI response
            response = requests.post(
                f"{API_URL}/api/chat/image/{backend_image_id}",
                json={"message": user_message, "image_id": backend_image_id}
            )
            
            if response.status_code == 200:
                # Extract the response text
                response_data = response.json()
                ai_response = response_data.get('response', {}).get('llm_analysis', {}).get('response', 'No response received')
                
                # Create new AI message in database
                ai_chat_message = ChatMessage.objects.create(
                    role='assistant',
                    content=ai_response,
                    session_id=session_id,
                    related_image=image
                )
                
                return JsonResponse({
                    'success': True,
                    'response': ai_response
                })
            else:
                return JsonResponse({
                    'error': f"Backend API error: {response.text}"
                }, status=response.status_code)
                
        except Exception as e:
            return JsonResponse({'error': f"Error: {str(e)}"}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
