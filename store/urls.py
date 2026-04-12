from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_home, name='store_home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/review/', views.add_review, name='add_review'),
]