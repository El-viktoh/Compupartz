from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


class Product(models.Model):
    CATEGORY_CHOICES = (
        ('laptop', 'Laptop'),
        ('part', 'Part'),
        ('accessories', 'Accessories'),
    )

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)

    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # =========================
    # ⭐ RATING METHODS
    # =========================
    def get_average_rating(self):
        avg = self.reviews.aggregate(avg=Avg("rating"))["avg"]
        return round(avg, 1) if avg else 0

    def get_review_count(self):
        return self.reviews.count()

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return self.product.name


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="reviews",   # ✅ IMPORTANT (used in rating)
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField()  # 1–5 stars
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐"