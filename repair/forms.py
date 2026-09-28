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
                "class": "w-full bg-[#F8FAFC] dark:bg-white/[0.04] border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:bg-white dark:focus:bg-[#1a1d24] focus:outline-none focus:ring-4 focus:ring-[#FF7200]/10 focus:border-[#FF7200] transition-all text-slate-800 dark:text-white text-sm shadow-sm",
            }),
            "manufacturer": forms.TextInput(attrs={
                "class": "w-full bg-[#F8FAFC] dark:bg-white/[0.04] border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:bg-white dark:focus:bg-[#1a1d24] focus:outline-none focus:ring-4 focus:ring-[#FF7200]/10 focus:border-[#FF7200] transition-all text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-gray-500 shadow-sm",
                "placeholder": "e.g. Apple, Dell, Lenovo, ASUS, HP",
            }),
            "device": forms.TextInput(attrs={
                "class": "w-full bg-[#F8FAFC] dark:bg-white/[0.04] border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:bg-white dark:focus:bg-[#1a1d24] focus:outline-none focus:ring-4 focus:ring-[#FF7200]/10 focus:border-[#FF7200] transition-all text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-gray-500 shadow-sm",
                "placeholder": "e.g. MacBook Pro M1 A2338 / XPS 15 9500",
            }),
            "issue_description": forms.Textarea(attrs={
                "class": "w-full bg-[#F8FAFC] dark:bg-white/[0.04] border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 h-32 resize-none focus:bg-white dark:focus:bg-[#1a1d24] focus:outline-none focus:ring-4 focus:ring-[#FF7200]/10 focus:border-[#FF7200] transition-all text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-gray-500 shadow-sm",
                "placeholder": "Please describe the symptoms observed (e.g. no power, flashing charging LED, flickering screen, liquid spill, overheating, blue screen errors)...",
            }),
            "diagnostic_image": forms.FileInput(attrs={
                "class": "hidden",
                "id": "diagnostic_image_input",
                "accept": "image/*",
            }),
            "customer_name": forms.TextInput(attrs={
                "class": "w-full bg-[#F8FAFC] dark:bg-white/[0.04] border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:bg-white dark:focus:bg-[#1a1d24] focus:outline-none focus:ring-4 focus:ring-[#FF7200]/10 focus:border-[#FF7200] transition-all text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-gray-500 shadow-sm",
                "placeholder": "e.g. Kwame Mensah",
            }),
            "customer_email": forms.EmailInput(attrs={
                "class": "w-full bg-[#F8FAFC] dark:bg-white/[0.04] border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:bg-white dark:focus:bg-[#1a1d24] focus:outline-none focus:ring-4 focus:ring-[#FF7200]/10 focus:border-[#FF7200] transition-all text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-gray-500 shadow-sm",
                "placeholder": "kwame@example.com",
            }),
            "customer_phone": forms.TextInput(attrs={
                "class": "w-full bg-[#F8FAFC] dark:bg-white/[0.04] border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:bg-white dark:focus:bg-[#1a1d24] focus:outline-none focus:ring-4 focus:ring-[#FF7200]/10 focus:border-[#FF7200] transition-all text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-gray-500 shadow-sm",
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
                "class": "w-full bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/40 focus:border-[#FF7200] transition-all text-slate-900 dark:text-white text-sm placeholder-slate-400 dark:placeholder-gray-500 shadow-sm",
                "placeholder": "e.g. John Doe",
            }),
            "customer_phone": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/40 focus:border-[#FF7200] transition-all text-slate-900 dark:text-white text-sm placeholder-slate-400 dark:placeholder-gray-500 shadow-sm",
                "placeholder": "+233 54 000 0000",
            }),
            "customer_email": forms.EmailInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/40 focus:border-[#FF7200] transition-all text-slate-900 dark:text-white text-sm placeholder-slate-400 dark:placeholder-gray-500 shadow-sm",
                "placeholder": "john@example.com (optional)",
            }),
            "part_needed": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/40 focus:border-[#FF7200] transition-all text-slate-900 dark:text-white text-sm placeholder-slate-400 dark:placeholder-gray-500 shadow-sm",
                "placeholder": "e.g. Battery, Retina Screen Assembly, Keyboard, DC Power Jack",
            }),
            "device_model": forms.TextInput(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 focus:outline-none focus:ring-2 focus:ring-[#FF7200]/40 focus:border-[#FF7200] transition-all text-slate-900 dark:text-white text-sm placeholder-slate-400 dark:placeholder-gray-500 shadow-sm",
                "placeholder": "e.g. Dell XPS 15 9500 / MacBook Pro M1 A2338",
            }),
            "condition_preference": forms.RadioSelect(attrs={
                "class": "hidden",
            }),
            "additional_details": forms.Textarea(attrs={
                "class": "w-full bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/10 rounded-xl px-4 sm:px-5 py-3.5 h-28 resize-none focus:outline-none focus:ring-2 focus:ring-[#FF7200]/40 focus:border-[#FF7200] transition-all text-slate-900 dark:text-white text-sm placeholder-slate-400 dark:placeholder-gray-500 shadow-sm",
                "placeholder": "Include part number, color, specifications, or any photos/links if known...",
            }),
        }
