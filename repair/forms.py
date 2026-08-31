from django import forms
from .models import RepairTicket, PartRequest


class RepairBookingForm(forms.ModelForm):
    class Meta:
        model = RepairTicket
        fields = [
            "customer_name",
            "customer_email",
            "customer_phone",
            "device_category",
            "manufacturer",
            "device",
            "issue_description",
            "diagnostic_image",
            "logistics_preference",
        ]

        widgets = {
            "device_category": forms.Select(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white text-sm",
            }),
            "manufacturer": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "e.g. Dell, ASUS, Lenovo",
            }),
            "device": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "e.g. XPS 15 9500 / S/N: 1A2B3C4D",
            }),
            "issue_description": forms.Textarea(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "Describe the failure mode. When did it start? Are there any error codes?",
            }),
            "diagnostic_image": forms.FileInput(attrs={
                "class": "hidden",
                "id": "diagnostic_image_input"
            }),
            "customer_name": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "John Doe",
            }),
            "customer_email": forms.EmailInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "john@example.com",
            }),
            "customer_phone": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "+233 54 000 0000",
            }),
            "logistics_preference": forms.RadioSelect(attrs={
                "class": "hidden",
            }),
        }


class PartRequestForm(forms.ModelForm):
    class Meta:
        model = PartRequest
        fields = [
            "customer_name",
            "customer_phone",
            "customer_email",
            "part_needed",
            "device_model",
            "condition_preference",
            "additional_details",
        ]

        widgets = {
            "customer_name": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/50 focus:border-[#FF7200] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "John Doe",
            }),
            "customer_phone": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/50 focus:border-[#FF7200] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "+233 54 000 0000",
            }),
            "customer_email": forms.EmailInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/50 focus:border-[#FF7200] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "john@example.com (optional)",
            }),
            "part_needed": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/50 focus:border-[#FF7200] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "e.g. Battery, Screen, Keyboard, Charging Port",
            }),
            "device_model": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/50 focus:border-[#FF7200] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "e.g. Dell XPS 15 9500",
            }),
            "condition_preference": forms.RadioSelect(attrs={
                "class": "hidden",
            }),
            "additional_details": forms.Textarea(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 h-28 resize-none focus:outline-none focus:ring-2 focus:ring-[#FF7200]/50 focus:border-[#FF7200] transition-all text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "Anything else that helps us source the right part (optional).",
            }),
        }
