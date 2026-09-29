from django.urls import path
from .views import home, signup, dashboard, update_profile, terms, privacy_policy, activate, contact, submit_testimonial, reviews_list

urlpatterns = [
    path('', home, name='home'),
    path('reviews/', reviews_list, name='reviews'),
    path('signup/', signup, name='signup'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/update/', update_profile, name='update_profile'),
    path('testimonial/submit/', submit_testimonial, name='submit_testimonial'),
    path('terms/', terms, name='terms'),
    path('privacy/', privacy_policy, name='privacy_policy'),
    path('contact/', contact, name='contact'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
]
