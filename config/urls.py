from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.auth_views import ThrottledPasswordResetView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('how-we-work/hub/', include('blog.urls')),
    path('repair/', include('repair.urls')),

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_reset/', ThrottledPasswordResetView.as_view(), name='password_reset'),

    # ✅ AUTH ROUTES
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
]

# Storefront is off while the site runs repair-only — set ENABLE_STORE=True
# in settings/env to bring store/cart/checkout/order-tracking/parts back.
if settings.ENABLE_STORE:
    urlpatterns += [
        path('store/', include('store.urls')),
        path('cart/', include('cart.urls')),
        path('order/', include('customer_orders.urls')),
        path('parts/', include('parts.urls')),
    ]

if settings.DEBUG:
    from django.shortcuts import render
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path(
            'dev/preview-password-reset-email/',
            lambda request: render(request, 'registration/password_reset_email.html', {
                'protocol': 'http',
                'domain': '127.0.0.1:8000',
                'uid': 'MQ',
                'token': 'preview-token-example',
            }),
            name='preview_password_reset_email',
        ),
    ]

