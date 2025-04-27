from django.db import models
import uuid
import os
from django.utils import timezone

def get_upload_path(instance, filename):
    """Function to generate a unique file path for uploaded images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('uploads', filename)

class DroneImage(models.Model):
    """Model for storing drone images"""
    image_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=get_upload_path)
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    # Backend reference
    backend_image_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata extracted from image
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True)
    camera_make = models.CharField(max_length=255, blank=True)
    camera_model = models.CharField(max_length=255, blank=True)
    
    # Analysis results
    analyzed = models.BooleanField(default=False)
    analysis_result = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"Image {self.image_id}"
    
    class Meta:
        ordering = ['-uploaded_at']

class AnalysisResult(models.Model):
    """Model for storing analysis results"""
    result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drone_image = models.ForeignKey(DroneImage, on_delete=models.CASCADE, related_name='results')
    created_at = models.DateTimeField(default=timezone.now)
    
    # Location data
    country = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    street = models.CharField(max_length=255, blank=True)
    neighborhood = models.CharField(max_length=255, blank=True)
    
    # Analysis data
    description = models.TextField(blank=True)
    confidence = models.CharField(max_length=50, blank=True)
    
    # Features detected
    architectural_features = models.JSONField(default=list, blank=True)
    landscape_features = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"Analysis for {self.drone_image}"
    
    class Meta:
        ordering = ['-created_at']

class ChatMessage(models.Model):
    """Model for storing chat messages"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=50)
    related_image = models.ForeignKey(DroneImage, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.role}: {self.content[:30]}..."
    
    class Meta:
        ordering = ['timestamp']
