from django.urls import path
from .views import home, signup, dashboard, update_profile, terms, privacy_policy, activate

urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/update/', update_profile, name='update_profile'),
    path('terms/', terms, name='terms'),
    path('privacy/', privacy_policy, name='privacy_policy'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
]


