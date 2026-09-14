from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Membership, Organization, User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=32, required=False)
    account_type = forms.ChoiceField(
        choices=User.AccountType.choices,
        widget=forms.RadioSelect,
        initial=User.AccountType.INDIVIDUAL,
    )
    organization_name = forms.CharField(max_length=150, required=False)
    organization_industry = forms.ChoiceField(
        choices=Organization.Industry.choices, required=False
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "username",
            "account_type",
            "organization_name",
            "organization_industry",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("account_type") == User.AccountType.ORGANIZATION:
            if not cleaned_data.get("organization_name"):
                self.add_error(
                    "organization_name",
                    "Please tell us your organization's name.",
                )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone_number = self.cleaned_data.get("phone_number", "")
        user.account_type = self.cleaned_data["account_type"]
        if commit:
            user.save()
            if user.account_type == User.AccountType.ORGANIZATION:
                org = Organization.objects.create(
                    name=self.cleaned_data["organization_name"],
                    industry=self.cleaned_data.get("organization_industry") or Organization.Industry.OTHER,
                    contact_email=user.email,
                    contact_phone=user.phone_number,
                    created_by=user,
                )
                Membership.objects.create(
                    user=user, organization=org, role=Membership.Role.OWNER
                )
        return user


class TeldemAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(attrs={"autofocus": True}),
    )


class InviteMemberForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=Membership.Role.choices, initial=Membership.Role.VIEWER)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "email")


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ("name", "industry", "contact_email", "contact_phone", "address")
