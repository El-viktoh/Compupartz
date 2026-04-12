from django.urls import path
from . import views
from .views import ajax_add_to_cart, ajax_update_cart

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('decrease/<int:product_id>/', views.decrease_cart_item, name='decrease_cart_item'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('paystack/<int:order_id>/', views.paystack_payment, name='paystack_payment'),
    path('ajax/add/', ajax_add_to_cart, name='ajax_add_to_cart'),
    path('ajax/update/', ajax_update_cart, name='ajax_update_cart'),
    path("ajax/", views.cart_ajax_get, name="cart_ajax_get"),
    path("ajax/count/", views.cart_count, name="cart_count"),

]
