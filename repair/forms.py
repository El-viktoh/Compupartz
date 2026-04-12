from django import forms
from .models import RepairTicket


class RepairBookingForm(forms.ModelForm):
    class Meta:
        model = RepairTicket
        fields = [
            "customer_name",
            "customer_email",
            "customer_phone",
            "device",
            "issue_description",
            "in_person",
        ]

        widgets = {
            "customer_name": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "Full Name",
            }),
            "customer_email": forms.EmailInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "Email Address",
            }),
            "customer_phone": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "Phone Number",
            }),
            "device": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "Laptop model (e.g. MacBook Pro, Dell XPS)",
            }),
            "issue_description": forms.Textarea(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-5 py-4 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-[#008BC6]/50 focus:border-[#008BC6] transition-all text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500",
                "placeholder": "Briefly describe the hardware or software issue...",
            }),
            "in_person": forms.CheckboxInput(attrs={
                "class": "h-5 w-5 text-[#008BC6] focus:ring-[#008BC6] rounded bg-white dark:bg-white/5 border-gray-200 dark:border-white/10",
            }),
        }
