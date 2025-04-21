from django.contrib import admin
from .models import DroneImage, AnalysisResult, ChatMessage

@admin.register(DroneImage)
class DroneImageAdmin(admin.ModelAdmin):
    list_display = ('image_id', 'title', 'uploaded_at', 'analyzed')
    list_filter = ('analyzed', 'uploaded_at')
    search_fields = ('title', 'description')
    readonly_fields = ('image_id', 'uploaded_at')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('result_id', 'drone_image', 'country', 'city', 'created_at')
    list_filter = ('country', 'city', 'created_at')
    search_fields = ('country', 'city', 'description')
    readonly_fields = ('result_id', 'created_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'role', 'content_preview', 'timestamp', 'session_id')
    list_filter = ('role', 'timestamp', 'session_id')
    search_fields = ('content', 'session_id')
    readonly_fields = ('message_id', 'timestamp')
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
