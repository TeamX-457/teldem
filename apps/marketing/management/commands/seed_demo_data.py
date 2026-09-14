"""Populate the database with a realistic, immediately-demoable dataset.

Creates: subscription plans, a superuser, a demo individual (B2C) account,
a demo organization (B2B) account with team members, devices for both,
~48 hours of historical sensor readings (with alerts where thresholds were
crossed), and a few published blog posts.

Safe to re-run: everything is created with get_or_create.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Membership, Organization
from apps.alerts.engine import evaluate_reading
from apps.billing.models import Subscription, SubscriptionPlan
from apps.devices.constants import metrics_for
from apps.devices.management.commands.simulate_readings import (
    _next_location,
    generate_reading_value,
)
from apps.devices.models import Device, SensorReading
from apps.marketing.models import BlogPost

User = get_user_model()

DEMO_PASSWORD = "TeldemDemo2026!"
ADMIN_PASSWORD = "TeldemAdmin2026!"

HISTORY_HOURS = 48
STEP_MINUTES = 30


class Command(BaseCommand):
    help = "Seed the database with demo plans, accounts, devices, readings and alerts."

    def handle(self, *args, **options):
        with transaction.atomic():
            self._run(options)

    def _run(self, options):
        self.stdout.write("Seeding TELDEM AI demo data...")

        self._seed_plans()
        admin = self._seed_superuser()
        household_user = self._seed_individual_account()
        org, org_owner = self._seed_organization_account()

        household_devices = self._seed_household_devices(household_user)
        org_devices = self._seed_org_devices(org)

        self._seed_subscription(user=household_user, tier=SubscriptionPlan.Tier.HOME)
        self._seed_subscription(organization=org, tier=SubscriptionPlan.Tier.BUSINESS)

        all_devices = list(household_devices) + list(org_devices)
        self._seed_history(all_devices)

        self._seed_blog_posts()

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo login credentials"))
        self.stdout.write(f"  Superuser (Django admin): admin / {ADMIN_PASSWORD}")
        self.stdout.write(f"  Individual account:       demo.household@teldem.ai / {DEMO_PASSWORD}")
        self.stdout.write(f"  Organization owner:       demo.business@teldem.ai / {DEMO_PASSWORD}")
        self.stdout.write(f"  Organization admin:       demo.manager@teldem.ai / {DEMO_PASSWORD}")
        self.stdout.write(f"  Organization viewer:      demo.staff@teldem.ai / {DEMO_PASSWORD}")

    # ------------------------------------------------------------------
    # Plans & accounts
    # ------------------------------------------------------------------

    def _seed_plans(self):
        plans = [
            dict(
                name="Starter",
                slug="starter",
                tier=SubscriptionPlan.Tier.STARTER,
                tagline="One device, full protection.",
                price_monthly=2500,
                price_device_from=45000,
                max_devices=1,
                order=1,
                features=[
                    "1 TELDEM Smart AI Device",
                    "Real-time alerts (app + SMS)",
                    "7-day sensor history",
                    "Email support",
                ],
            ),
            dict(
                name="Home",
                slug="home",
                tier=SubscriptionPlan.Tier.HOME,
                tagline="Whole-household coverage.",
                price_monthly=4500,
                price_device_from=75000,
                max_devices=4,
                order=2,
                is_featured=True,
                features=[
                    "Up to 4 TELDEM Smart AI Devices",
                    "Real-time alerts (app, SMS, email)",
                    "30-day sensor history",
                    "Arm / disarm security devices",
                    "Priority support",
                ],
            ),
            dict(
                name="Business",
                slug="business",
                tier=SubscriptionPlan.Tier.BUSINESS,
                tagline="For restaurants, hotels, schools & offices.",
                price_monthly=15000,
                price_device_from=150000,
                max_devices=20,
                order=3,
                features=[
                    "Up to 20 TELDEM Smart AI Devices",
                    "Team accounts with roles",
                    "90-day sensor history",
                    "Multi-location dashboards",
                    "Dedicated account manager",
                ],
            ),
            dict(
                name="Enterprise",
                slug="enterprise",
                tier=SubscriptionPlan.Tier.ENTERPRISE,
                tagline="Bulk deployments & custom integrations.",
                price_monthly=None,
                price_device_from=None,
                max_devices=None,
                order=4,
                is_contact_sales=True,
                features=[
                    "Unlimited TELDEM Smart AI Devices",
                    "Custom API & data integrations",
                    "Bulk / partner pricing",
                    "SLA-backed support",
                ],
            ),
        ]
        for data in plans:
            SubscriptionPlan.objects.update_or_create(
                slug=data["slug"], defaults=data
            )

    def _seed_superuser(self):
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults=dict(
                email="admin@teldem.ai",
                first_name="TELDEM",
                last_name="Ops",
                is_staff=True,
                is_superuser=True,
                account_type=User.AccountType.INDIVIDUAL,
            ),
        )
        if created:
            admin.set_password(ADMIN_PASSWORD)
            admin.save()
        return admin

    def _seed_individual_account(self):
        user, created = User.objects.get_or_create(
            username="demo_household",
            defaults=dict(
                email="demo.household@teldem.ai",
                first_name="Ada",
                last_name="Okafor",
                phone_number="+2348012345678",
                account_type=User.AccountType.INDIVIDUAL,
                has_completed_onboarding=True,
                is_email_verified=True,
            ),
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user

    def _seed_organization_account(self):
        owner, created = User.objects.get_or_create(
            username="demo_business",
            defaults=dict(
                email="demo.business@teldem.ai",
                first_name="Tunde",
                last_name="Balogun",
                phone_number="+2348022223333",
                account_type=User.AccountType.ORGANIZATION,
                has_completed_onboarding=True,
                is_email_verified=True,
            ),
        )
        if created:
            owner.set_password(DEMO_PASSWORD)
            owner.save()

        org, _ = Organization.objects.get_or_create(
            name="Lagos Bistro Group",
            defaults=dict(
                industry=Organization.Industry.RESTAURANT,
                contact_email="ops@lagosbistro.example",
                contact_phone="+2348022223333",
                address="14 Admiralty Way, Lekki Phase 1, Lagos",
                created_by=owner,
            ),
        )
        Membership.objects.get_or_create(
            user=owner, organization=org, defaults={"role": Membership.Role.OWNER}
        )

        manager, created = User.objects.get_or_create(
            username="demo_manager",
            defaults=dict(
                email="demo.manager@teldem.ai",
                first_name="Chioma",
                last_name="Eze",
                account_type=User.AccountType.ORGANIZATION,
                has_completed_onboarding=True,
            ),
        )
        if created:
            manager.set_password(DEMO_PASSWORD)
            manager.save()
        Membership.objects.get_or_create(
            user=manager, organization=org, defaults={"role": Membership.Role.ADMIN}
        )

        staff, created = User.objects.get_or_create(
            username="demo_staff",
            defaults=dict(
                email="demo.staff@teldem.ai",
                first_name="Bola",
                last_name="Ogundele",
                account_type=User.AccountType.ORGANIZATION,
                has_completed_onboarding=True,
            ),
        )
        if created:
            staff.set_password(DEMO_PASSWORD)
            staff.save()
        Membership.objects.get_or_create(
            user=staff, organization=org, defaults={"role": Membership.Role.VIEWER}
        )

        return org, owner

    def _seed_subscription(self, tier, user=None, organization=None):
        plan = SubscriptionPlan.objects.get(tier=tier)
        owner_kwargs = {"organization": organization} if organization else {"user": user}
        Subscription.objects.get_or_create(
            plan=plan,
            defaults=dict(
                status=Subscription.Status.ACTIVE,
                current_period_end=timezone.now() + timedelta(days=30),
                payment_provider="simulated",
                **owner_kwargs,
            ),
            **owner_kwargs,
        )

    # ------------------------------------------------------------------
    # Devices
    # ------------------------------------------------------------------

    def _seed_household_devices(self, user):
        specs = [
            (Device.DeviceType.FRIDGE, "Kitchen Fridge", "Kitchen", False),
            (Device.DeviceType.GAS, "Cooking Gas Cylinder", "Kitchen", False),
            (Device.DeviceType.HOME_OFFICE, "Living Room Sensor", "Living Room", True),
        ]
        return self._create_devices(specs, user=user)

    def _seed_org_devices(self, org):
        specs = [
            (Device.DeviceType.FRIDGE, "Walk-in Fridge", "Main Kitchen", False),
            (Device.DeviceType.FRIDGE, "Bar Fridge", "Rooftop Bar", False),
            (Device.DeviceType.GAS, "Cold Room Gas Bank", "Store Room", False),
            (Device.DeviceType.VEHICLE, "Delivery Van 1", "Fleet Bay", True),
            (Device.DeviceType.HOME_OFFICE, "Front Entrance", "Main Entrance", True),
            (Device.DeviceType.HOME_OFFICE, "Store Room Sensor", "Store Room", True),
        ]
        return self._create_devices(specs, organization=org)

    def _create_devices(self, specs, user=None, organization=None):
        devices = []
        for device_type, name, location, armed in specs:
            owner_kwargs = {"organization": organization} if organization else {"user": user}
            device, _ = Device.objects.get_or_create(
                name=name,
                **owner_kwargs,
                defaults=dict(
                    device_type=device_type,
                    location_label=location,
                    status=Device.Status.ONLINE,
                    is_armed=armed,
                    install_date=timezone.localdate() - timedelta(days=30),
                ),
            )
            devices.append(device)
        return devices

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def _seed_history(self, devices):
        now = timezone.now()
        steps = int(HISTORY_HOURS * 60 / STEP_MINUTES)
        start = now - timedelta(minutes=steps * STEP_MINUTES)

        # Idempotent re-runs: wipe previously-seeded history for these
        # devices rather than piling up duplicates.
        SensorReading.objects.filter(device__in=devices).delete()
        from apps.alerts.models import Alert
        Alert.objects.filter(device__in=devices).delete()

        for device in devices:
            metrics = metrics_for(device.device_type)
            for i in range(steps + 1):
                ts = start + timedelta(minutes=i * STEP_MINUTES)
                for metric, cfg in metrics.items():
                    if cfg["kind"] == "location":
                        SensorReading.objects.create(
                            device=device, metric=metric, value=0.0,
                            unit=_next_location(), timestamp=ts,
                        )
                        continue
                    value = generate_reading_value(device, metric, cfg)
                    reading = SensorReading.objects.create(
                        device=device, metric=metric, value=value,
                        unit=cfg["unit"], timestamp=ts,
                    )
                    evaluate_reading(reading)

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def _seed_blog_posts(self):
        posts = [
            dict(
                title="Introducing TELDEM AI: Smarter Spaces, Safer Lives",
                slug="introducing-teldem-ai",
                excerpt="Why we built a single AI platform to watch over your fridge, gas, vehicle and home.",
                body=(
                    "For years, monitoring your home or business meant juggling separate, "
                    "single-purpose gadgets that only show raw numbers. TELDEM AI unifies "
                    "sensing, analysis and alerting into one platform that tells you what "
                    "is actually happening — before it becomes a crisis."
                ),
            ),
            dict(
                title="How Nigerian Restaurants Are Cutting Spoilage Losses with AI",
                slug="restaurants-cutting-spoilage-losses",
                excerpt="A look at how proactive cold-chain monitoring protects margins.",
                body=(
                    "Food spoilage from silent fridge failures is one of the largest hidden "
                    "costs in hospitality. TELDEM's Smart Fridge devices watch temperature "
                    "trends continuously and alert kitchen managers long before stock is lost."
                ),
            ),
            dict(
                title="Never Run Out of Gas Again: Inside TELDEM Smart Gas",
                slug="never-run-out-of-gas-again",
                excerpt="Real-time gas level tracking for homes and businesses.",
                body=(
                    "Running out of cooking gas mid-service, or mid-meal, is entirely "
                    "preventable. TELDEM Smart Gas tracks levels in real time and warns you "
                    "days ahead — not minutes."
                ),
            ),
        ]
        for data in posts:
            BlogPost.objects.get_or_create(
                slug=data["slug"],
                defaults=dict(
                    title=data["title"],
                    excerpt=data["excerpt"],
                    body=data["body"],
                    is_published=True,
                    published_at=timezone.now() - timedelta(days=len(data["title"]) % 10),
                ),
            )
