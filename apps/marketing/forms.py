from django import forms

from .models import ContactSubmission


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "phone", "interest_type", "company_name", "message"]
        widgets = {
            "interest_type": forms.RadioSelect,
            "message": forms.Textarea(attrs={"rows": 5}),
        }
