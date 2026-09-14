"""Remove the seeded demo records created by `seed_demo_data`.

Deletes the demo household/business/manager/staff accounts (which
cascades their organization, memberships, devices, sensor readings,
alerts and subscriptions) and the seeded blog posts.

Deliberately left alone:
- The `admin` superuser, so you aren't locked out of /admin/. Delete it
  yourself (or change its password) once you have your own admin account.
- SubscriptionPlan rows (Starter/Home/Business/Enterprise), since the
  public pricing page reads live from these — they're product
  configuration, not fake/demo data. Manage them in Django admin.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Organization
from apps.marketing.models import BlogPost

User = get_user_model()

DEMO_USERNAMES = ["demo_household", "demo_business", "demo_manager", "demo_staff"]
DEMO_BLOG_SLUGS = [
    "introducing-teldem-ai",
    "restaurants-cutting-spoilage-losses",
    "never-run-out-of-gas-again",
]


class Command(BaseCommand):
    help = "Delete seeded demo users/org/devices/readings/alerts/subscriptions/blog posts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--include-admin",
            action="store_true",
            help="Also delete the seeded 'admin' superuser account.",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            users_qs = User.objects.filter(username__in=DEMO_USERNAMES)
            user_count = users_qs.count()
            users_qs.delete()

            # Deleting the demo users removes their Memberships, but an
            # Organization isn't owned by a single User FK - it's only
            # linked via Membership - so orphaned demo orgs (no members
            # left) need to be cleaned up explicitly. This cascades to
            # their Devices, SensorReadings, Alerts and Subscriptions.
            orphaned_orgs_qs = Organization.objects.filter(memberships__isnull=True)
            org_count = orphaned_orgs_qs.count()
            orphaned_orgs_qs.delete()

            posts_qs = BlogPost.objects.filter(slug__in=DEMO_BLOG_SLUGS)
            post_count = posts_qs.count()
            posts_qs.delete()

            admin_deleted = False
            if options["include_admin"]:
                admin_qs = User.objects.filter(username="admin")
                admin_deleted = admin_qs.exists()
                admin_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Removed {user_count} demo user(s), {org_count} orphaned "
                f"organization(s) (cascading their devices, readings, alerts "
                f"and subscriptions), and {post_count} demo blog post(s)."
            )
        )
        if admin_deleted:
            self.stdout.write(self.style.WARNING("Also removed the 'admin' superuser."))
        elif options["include_admin"]:
            self.stdout.write("No 'admin' superuser found to remove.")
        else:
            self.stdout.write(
                "Kept the 'admin' superuser and SubscriptionPlan rows — "
                "see this command's docstring for why."
            )
