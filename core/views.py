from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

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
    faqs = FAQ.objects.filter(is_published=True)
    latest_posts = Post.objects.filter(status='published').order_by('-created_at')[:3]
    featured_videos = Video.objects.filter(is_featured=True)

    return render(request, "home.html", {
        "faqs": faqs,
        "latest_posts": latest_posts,
        "featured_videos": featured_videos,
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


from repair.models import RepairTicket
from .forms import UserUpdateForm, ProfileUpdateForm

# =========================
# ⭐ USER DASHBOARD & PROFILE
# =========================
@login_required
def dashboard(request):
    active_repairs = RepairTicket.objects.filter(
        user=request.user,
        status__in=['pending', 'in_progress']
    ).order_by('-created_at')
    
    past_repairs = RepairTicket.objects.filter(
        user=request.user,
        status='completed'
    ).order_by('-created_at')

    # ✅ ENSURE PROFILE EXISTS (Fixes crash for existing users)
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # ✅ GET FORMS FOR MODAL
    u_form = UserUpdateForm(instance=request.user)
    p_form = ProfileUpdateForm(instance=profile)

    return render(request, "account/dashboard.html", {
        "active_repairs": active_repairs,
        "past_repairs": past_repairs,
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

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message_body = request.POST.get("message", "").strip()

        if name and email and subject and message_body:
            try:
                EmailMessage(
                    subject=f"[Contact Form] {subject}",
                    body=f"From: {name} <{email}>\n\n{message_body}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.SERVER_EMAIL],
                    reply_to=[email],
                ).send(fail_silently=False)
                messages.success(request, "Your message has been sent. We'll get back to you shortly.")
            except Exception as e:
                logger.error(f"Contact form email error: {str(e)}")
                messages.error(request, "We couldn't send your message right now. Please try again later.")
            return redirect("contact")

        messages.error(request, "Please fill in all fields.")

    return render(request, "core/contact.html")