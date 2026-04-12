from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

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

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']
        widgets = {
            "avatar": forms.FileInput(attrs={
                "class": "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#008BC6]/10 file:text-[#008BC6] hover:file:bg-[#008BC6]/20 transition-all cursor-pointer",
            }),
        }
