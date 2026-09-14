from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from .models import Subscription, SubscriptionPlan


def _owner_kwargs(user):
    organization = user.primary_organization
    if organization:
        return {"organization": organization}
    return {"user": user}


@login_required
def billing_overview(request):
    owner_kwargs = _owner_kwargs(request.user)
    subscription = (
        Subscription.objects.filter(**owner_kwargs).select_related("plan").first()
    )
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(
        request,
        "billing/overview.html",
        {"subscription": subscription, "plans": plans},
    )


@login_required
def plan_subscribe(request, slug):
    plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)
    owner_kwargs = _owner_kwargs(request.user)

    if plan.is_contact_sales:
        messages.info(
            request,
            f"Thanks for your interest in {plan.name}! Our team will reach out to "
            "structure an enterprise agreement.",
        )
        return redirect("marketing:business")

    if request.method == "POST":
        # Payment gateway integration point: swap this block for a real
        # Paystack/Flutterwave charge + webhook confirmation.
        Subscription.objects.filter(**owner_kwargs).exclude(
            status=Subscription.Status.CANCELED
        ).update(status=Subscription.Status.CANCELED)

        Subscription.objects.create(
            plan=plan,
            status=Subscription.Status.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30),
            payment_provider="simulated",
            **owner_kwargs,
        )
        messages.success(request, f"You're now on the {plan.name} plan.")
        return redirect("billing:overview")

    return render(request, "billing/confirm_subscribe.html", {"plan": plan})
