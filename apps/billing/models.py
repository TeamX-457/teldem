from django.conf import settings
from django.db import models


class SubscriptionPlan(models.Model):
    class Tier(models.TextChoices):
        STARTER = "starter", "Starter"
        HOME = "home", "Home"
        BUSINESS = "business", "Business"
        ENTERPRISE = "enterprise", "Enterprise"

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    tier = models.CharField(max_length=20, choices=Tier.choices, unique=True)
    tagline = models.CharField(max_length=150, blank=True)
    price_monthly = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Monthly AI subscription price in NGN. Blank = custom/contact sales.",
    )
    price_device_from = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Starting one-time device price in NGN.",
    )
    max_devices = models.PositiveIntegerField(
        null=True, blank=True, help_text="Blank = unlimited."
    )
    features = models.JSONField(default=list, blank=True)
    is_contact_sales = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIALING = "trialing", "Trialing"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    # Stubbed fields so a real gateway (Paystack/Flutterwave) can be wired
    # in later without a schema change.
    payment_provider = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        owner = self.organization.name if self.organization_id else self.user
        return f"{owner} - {self.plan.name} ({self.status})"

    @property
    def owner_display(self):
        if self.organization_id:
            return self.organization.name
        if self.user_id:
            return self.user.get_full_name() or self.user.username
        return "Unassigned"

    @property
    def is_active(self):
        return self.status in (self.Status.ACTIVE, self.Status.TRIALING)
