from django.db import models
import re

class Video(models.Model):
    title = models.CharField(max_length=255, help_text="Subtle title for the media briefing.")
    video_url = models.URLField(help_text="Link to YouTube, Vimeo, or social media video.")
    thumbnail = models.ImageField(upload_to='videos/thumbnails/', null=True, blank=True, help_text="Optional. If left blank, we'll try to fetch the YouTube placeholder.")
    is_featured = models.BooleanField(default=True, help_text="Should this appear in the homepage carousel?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        
        # Regex to extract YouTube ID
        regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        match = re.search(regex, self.video_url)
        if match:
            video_id = match.group(1)
            return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            
        return "/static/images/placeholder_video.jpg"

    def __str__(self):
        return self.title
