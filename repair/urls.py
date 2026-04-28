from django.urls import path
from . import views

urlpatterns = [
    path('', views.repair_home, name='repair_home'),
    path('book/', views.book_repair, name='book_repair'),

    # Repair success page
    path('success/<uuid:ticket_id>/', views.repair_success, name='repair_success'),

    # ✅ UPDATED — allow simple IDs like "R-6"
    path('track/', views.track_repair_lookup, name='track_repair_lookup'),
    path('track/<str:ticket_id>/', views.track_repair, name='track_repair'),
    path('my-repairs/', views.my_repairs, name='my_repairs'),
]
