from django.contrib import admin
from django.utils.html import format_html
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'thumbnail_preview', 'is_featured', 'created_at')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('title', 'video_url')
    
    def thumbnail_preview(self, obj):
        url = obj.get_thumbnail_url
        if url:
            return format_html(
                '<img src="{}" style="width: 70px; height: 42px; object-fit: cover; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);" />',
                url
            )
        return "No Image"
    thumbnail_preview.short_description = "Thumbnail"

