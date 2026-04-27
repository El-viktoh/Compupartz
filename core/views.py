from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from store.models import Product, Wishlist
from .models import FAQ, Profile
from blog.models import Post
from media_hub.models import Video
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.contrib import messages

# =========================
# HOME
# =========================
def home(request):
    featured_products = Product.objects.filter(available=True)[:6]
    faqs = FAQ.objects.filter(is_published=True)
    latest_posts = Post.objects.filter(status='published').order_by('-created_at')[:3]
    featured_videos = Video.objects.filter(is_featured=True)

    # ✅ attach rating data
    for product in featured_products:
        product.avg_rating = product.get_average_rating()
        product.review_count = product.get_review_count()

    # ✅ get wishlist for hearts
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, "home.html", {
        "featured_products": featured_products,
        "faqs": faqs,
        "latest_posts": latest_posts,
        "featured_videos": featured_videos,
        "wishlist_ids": wishlist_ids
    })


from .forms import RegistrationForm

from django.db import transaction
from .utils import send_activation_email
import logging

logger = logging.getLogger(__name__)

# =========================
# SIGNUP
# =========================
def signup(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False  # ✅ Deactivate account until email confirmation
                    user.save()

                    # ✅ SEND ACTIVATION EMAIL
                    domain = request.get_host()
                    if not send_activation_email(user, domain):
                        raise Exception("Failed to send email")

                # If we reach here, email was sent successfully
                return render(request, "registration/account_activation_sent.html")

            except Exception as e:
                # ❌ LOG THE ERROR ON SERVER
                logger.error(f"Signup Email Error: {str(e)}")
                
                # ❌ Inform user and allow them to fix email/try again
                messages.error(request, "We couldn't send the activation email. Please check your email address or try again later.")
                # The transaction.atomic() handles the rollback of the user creation automatically

    else:
        form = RegistrationForm()

    return render(request, "registration/signup.html", {
        "form": form
    })

# =========================
# ACTIVATE ACCOUNT
# =========================
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        return render(request, "registration/account_activation_invalid.html")


from customer_orders.models import Order
from repair.models import RepairTicket
from .forms import UserUpdateForm, ProfileUpdateForm

# =========================
# DASHBOARD
# =========================
@login_required
def dashboard(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    repairs = RepairTicket.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    # ✅ WISHLIST DATA
    wishlist_items = Wishlist.objects.filter(user=request.user).order_by('-created_at')[:4]
    wishlist_ids = wishlist_items.values_list('product_id', flat=True)

    # ✅ attach product image from first order item
    for order in orders:
        first_item = order.items.first()

        if first_item and hasattr(first_item, "product") and first_item.product and first_item.product.image:
            order.image = first_item.product.image.url
        else:
            order.image = None

    # ✅ ENSURE PROFILE EXISTS (Fixes crash for existing users)
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # ✅ GET FORMS FOR MODAL
    u_form = UserUpdateForm(instance=request.user)
    p_form = ProfileUpdateForm(instance=profile)

    return render(request, "account/dashboard.html", {
        "orders": orders,
        "repairs": repairs,
        "wishlist_items": wishlist_items,
        "wishlist_ids": wishlist_ids,
        "u_form": u_form,
        "p_form": p_form,
    })


# =========================
# UPDATE PROFILE
# =========================
@login_required
def update_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        
        # ✅ ENSURE PROFILE EXISTS
        profile, created = Profile.objects.get_or_create(user=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('dashboard')

    return redirect('dashboard')

# =========================
# TERMS & PRIVACY
# =========================
def terms(request):
    return render(request, "core/terms.html")

def privacy_policy(request):
    return render(request, "core/privacy.html")