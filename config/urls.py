from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('how-we-work/hub/', include('blog.urls')),
    path('repair/', include('repair.urls')),

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

