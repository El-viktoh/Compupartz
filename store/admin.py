from django.contrib import admin
from .models import Product, ProductImage, Review, Variation, VariationCategory


# ================= IMAGE INLINE =================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


# ================= VARIATION INLINE =================
class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1


# ================= PRODUCT ADMIN =================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'condition', 'price', 'stock_count', 'available')
    list_filter = ('category', 'condition', 'available')
    search_fields = ('name',)
    radio_fields = {'condition': admin.HORIZONTAL}
    inlines = [ProductImageInline, VariationInline]


# ================= VARIATION CATEGORY =================
@admin.register(VariationCategory)
class VariationCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


# ================= REVIEW ADMIN =================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")