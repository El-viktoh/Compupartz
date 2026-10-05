from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile


def is_unverified_signup(user):
    """A self-registered account that never proved it owns its email address."""
    if user.is_active or user.is_staff or user.is_superuser or user.last_login is not None:
        return False
    if user.socialaccount_set.exists():
        return False
    from repair.models import RepairTicket, PartRequest
    return not (RepairTicket.objects.filter(user=user).exists() or PartRequest.objects.filter(user=user).exists())


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        "placeholder": "First Name",
        "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-brandOrange/50 focus:border-brandOrange transition-all hover:border-brandOrange/30 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        "placeholder": "Last Name",
        "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-brandOrange/50 focus:border-brandOrange transition-all hover:border-brandOrange/30 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        "placeholder": "Email Address",
        "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-brandOrange/50 focus:border-brandOrange transition-all hover:border-brandOrange/30 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
    }))

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({
                "placeholder": "Username",
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-brandOrange/50 focus:border-brandOrange transition-all hover:border-brandOrange/30 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
            })

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if email and any(not is_unverified_signup(u) for u in User.objects.filter(email__iexact=email)):
            raise forms.ValidationError(
                "An account with this email already exists. Try logging in or resetting your password instead."
            )
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and any(not is_unverified_signup(u) for u in User.objects.filter(username__iexact=username)):
            raise ValidationError(self.instance.unique_error_message(User, ["username"]))
        return username

    def validate_unique(self):
        # Username uniqueness is enforced in clean_username so abandoned, unverified
        # sign-ups don't lock the name (or email) away from the person retrying.
        exclude = self._get_validation_exclusions()
        exclude.add("username")
        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError as e:
            self._update_errors(e)

    def replace_unverified_conflicts(self):
        """Delete abandoned, unverified accounts that hold this email or username."""
        q = Q(email__iexact=self.cleaned_data["email"]) | Q(username__iexact=self.cleaned_data["username"])
        removed = 0
        for user in User.objects.filter(q):
            if is_unverified_signup(user):
                user.delete()
                removed += 1
        return removed

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-brandOrange/50 focus:border-brandOrange transition-all hover:border-brandOrange/30 text-gray-900 dark:text-white",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-brandOrange/50 focus:border-brandOrange transition-all hover:border-brandOrange/30 text-gray-900 dark:text-white",
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-brandOrange/50 focus:border-brandOrange transition-all hover:border-brandOrange/30 text-gray-900 dark:text-white",
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another account is already using this email address.")
        return email

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']
        widgets = {
            "avatar": forms.FileInput(attrs={
                "class": "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#008BC6]/10 file:text-[#008BC6] hover:file:bg-[#008BC6]/20 transition-all cursor-pointer",
            }),
        }
