from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from apps.devices.models import Device

from .forms import (
    InviteMemberForm,
    OrganizationForm,
    ProfileForm,
    SignUpForm,
    TeldemAuthenticationForm,
)
from .models import Membership, User


class TeldemLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = TeldemAuthenticationForm
    redirect_authenticated_user = True


class TeldemLogoutView(LogoutView):
    next_page = "marketing:home"


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to TELDEM AI, {user.first_name}! Let's get your first device online.",
            )
            return redirect("accounts:onboarding")
    else:
        form = SignUpForm(initial={"account_type": User.AccountType.INDIVIDUAL})

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def onboarding_view(request):
    user = request.user
    device_count = Device.objects.filter_for_owner(user).count()

    if request.method == "POST":
        user.has_completed_onboarding = True
        user.save(update_fields=["has_completed_onboarding"])
        return redirect("dashboard:home")

    return render(
        request,
        "accounts/onboarding.html",
        {"device_count": device_count},
    )


@login_required
def profile_view(request):
    user = request.user
    membership = user.primary_membership
    organization = membership.organization if membership else None

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        org_form = OrganizationForm(
            request.POST, instance=organization
        ) if organization else None
        if form.is_valid() and (org_form is None or org_form.is_valid()):
            form.save()
            if org_form is not None:
                org_form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=user)
        org_form = OrganizationForm(instance=organization) if organization else None

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "org_form": org_form,
            "organization": organization,
            "membership": membership,
        },
    )


@login_required
def team_view(request):
    user = request.user
    membership = user.primary_membership

    if not membership:
        messages.info(request, "Team management is available for organization accounts.")
        return redirect("dashboard:home")

    organization = membership.organization
    can_manage = membership.role in (Membership.Role.OWNER, Membership.Role.ADMIN)

    if request.method == "POST" and can_manage:
        form = InviteMemberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower().strip()
            role = form.cleaned_data["role"]
            try:
                invited_user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.warning(
                    request,
                    f"No TELDEM account found for {email} yet. Ask them to sign up, "
                    "then invite them again.",
                )
            else:
                _, created = Membership.objects.get_or_create(
                    user=invited_user,
                    organization=organization,
                    defaults={"role": role},
                )
                if created:
                    messages.success(request, f"{email} added to {organization.name}.")
                else:
                    messages.info(request, f"{email} is already a member.")
            return redirect("accounts:team")
    else:
        form = InviteMemberForm()

    members = organization.memberships.select_related("user").all()

    return render(
        request,
        "accounts/team.html",
        {
            "organization": organization,
            "members": members,
            "form": form,
            "can_manage": can_manage,
        },
    )
