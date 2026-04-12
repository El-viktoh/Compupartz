from django.contrib import admin
from .models import Post, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'author', 'category')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    # Simple formatting for content field in admin if needed
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category', 'status')
        }),
        ('Content', {
            'fields': ('featured_image', 'excerpt', 'content', 'reading_time')
        }),
    )
