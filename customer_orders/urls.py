from django.urls import path
from .views import verify_payment, track_lookup, track_order

urlpatterns = [
    path("verify/<str:reference>/", verify_payment, name="verify_payment"),
    path("track/", track_lookup, name="track_lookup"),
    path("track/<int:order_id>/", track_order, name="track_order"),
]
