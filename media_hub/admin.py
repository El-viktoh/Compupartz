from django.contrib import admin
from django.utils.html import format_html
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'thumbnail_preview', 'is_featured', 'created_at')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('title', 'video_url')
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 4px;" />', obj.thumbnail.url)
        return "No Image"
    thumbnail_preview.short_description = "Preview"
