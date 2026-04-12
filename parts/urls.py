from django.urls import path
from .views import parts_home

urlpatterns = [
    path('', parts_home, name='parts_home'),
]
