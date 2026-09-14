from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    """TELDEM's user model.

    Every user is fundamentally an individual (B2C) account unless they are
    also linked to an Organization via a Membership, which flips their
    experience into the B2B / team context.
    """

    class AccountType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual / Household"
        ORGANIZATION = "organization", "Business / Organization"

    account_type = models.CharField(
        max_length=20, choices=AccountType.choices, default=AccountType.INDIVIDUAL
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    is_email_verified = models.BooleanField(default=False)
    has_completed_onboarding = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_organization_account(self):
        return self.account_type == self.AccountType.ORGANIZATION

    @property
    def primary_organization(self):
        membership = self.memberships.select_related("organization").first()
        return membership.organization if membership else None

    @property
    def primary_membership(self):
        return self.memberships.select_related("organization").first()


class Organization(models.Model):
    class Industry(models.TextChoices):
        RESTAURANT = "restaurant", "Restaurant / Food Service"
        HOTEL = "hotel", "Hotel / Hospitality"
        SCHOOL = "school", "School / Campus"
        OFFICE = "office", "Office / Corporate"
        ESTATE = "estate", "Residential Estate"
        LOGISTICS = "logistics", "Logistics / Fleet"
        RETAIL = "retail", "Retail"
        ENERGY = "energy", "Gas / Energy"
        OTHER = "other", "Other"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    industry = models.CharField(
        max_length=20, choices=Industry.choices, default=Industry.OTHER
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="organizations_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:150]
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        return self.memberships.count()

    @property
    def device_count(self):
        return self.devices.count()


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        VIEWER = "viewer", "Viewer"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organization")
        ordering = ["-role", "joined_at"]

    def __str__(self):
        return f"{self.user} @ {self.organization} ({self.role})"
