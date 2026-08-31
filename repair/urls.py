from django.urls import path
from . import views

urlpatterns = [
    path('', views.repair_home, name='repair_home'),
    path('book/', views.book_repair, name='book_repair'),

    # Repair success page
    path('success/<int:ticket_id>/', views.repair_success, name='repair_success'),

    # Parts request
    path('request-part/', views.request_part, name='request_part'),
    path('request-part/success/<int:request_id>/', views.part_request_success, name='part_request_success'),

    # ✅ UPDATED — allow simple IDs like "R-6"
    path('track/', views.track_repair_lookup, name='track_repair_lookup'),
    path('track/<str:ticket_id>/', views.track_repair, name='track_repair'),
    path('my-repairs/', views.my_repairs, name='my_repairs'),

    # Chat Edit / Delete
    path('message/<int:message_id>/edit/', views.edit_repair_message, name='edit_repair_message'),
    path('message/<int:message_id>/delete/', views.delete_repair_message, name='delete_repair_message'),
]
