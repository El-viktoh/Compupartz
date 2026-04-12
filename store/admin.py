from django.contrib import admin
from .models import Product, ProductImage, Review


# ================= IMAGE INLINE =================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


# ================= PRODUCT ADMIN =================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available')
    list_filter = ('category', 'available')
    search_fields = ('name',)
    inlines = [ProductImageInline]


# ================= REVIEW ADMIN =================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")