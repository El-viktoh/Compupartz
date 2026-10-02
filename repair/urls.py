from django.urls import path
from . import views

urlpatterns = [
    path('', views.repair_home, name='repair_home'),
    path('reviews/', views.reviews_redirect, name='repair_reviews'),
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

    # 🎯 Formal Quotation Desk (Staff Only)
    path('staff/quote/repair/<str:ticket_id>/', views.staff_create_repair_quote, name='staff_create_repair_quote'),
    path('staff/quote/part/<str:request_id>/', views.staff_create_part_quote, name='staff_create_part_quote'),

    # 🎯 Customer Quote Approvals
    path('quote/repair/<str:ticket_id>/approve/', views.customer_approve_repair_quote, name='customer_approve_repair_quote'),
    path('quote/repair/<str:ticket_id>/decline/', views.customer_decline_repair_quote, name='customer_decline_repair_quote'),
    path('quote/part/<str:request_id>/approve/', views.customer_approve_part_quote, name='customer_approve_part_quote'),

    # ⚙️ Part Request Tracking & Quotes
    path('track-part/', views.track_part_lookup, name='track_part_lookup'),
    path('track-part/<str:request_id>/', views.track_part, name='track_part'),

    # 📧 Email Previews
    path('preview-quote/', views.preview_repair_quote_email, name='preview_repair_quote_email'),
    path('preview-part-quote/', views.preview_part_quote_email, name='preview_part_quote_email'),

    # 🩺 Diagnostic Check
    path('diagnostic-check/', views.diagnostic_check, name='diagnostic_check'),
]


