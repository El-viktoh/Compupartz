from django.urls import path
from .views import verify_payment, track_lookup, track_order, my_orders

urlpatterns = [
    path("verify/<str:reference>/", verify_payment, name="verify_payment"),
    path("track/", track_lookup, name="track_lookup"),
    path("track/<int:order_id>/", track_order, name="track_order"),
    path("my-orders/", my_orders, name="my_orders"),
]
