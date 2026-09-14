"""Lightweight in-process scheduler for the sensor simulation.

Runs `simulate_readings` on a fixed interval using APScheduler, so the demo
stays "alive" without needing Celery/Redis. Intended for local/demo use -
in production, prefer an OS-level cron job or Task Scheduler entry calling
`manage.py simulate_readings` directly.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run simulate_readings on a recurring interval until interrupted (Ctrl+C)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval-seconds",
            type=int,
            default=60,
            help="Seconds between simulation rounds (default: 60).",
        )

    def handle(self, *args, **options):
        interval = options["interval_seconds"]
        scheduler = BlockingScheduler()

        def job():
            call_command("simulate_readings")

        scheduler.add_job(job, "interval", seconds=interval, next_run_time=None, id="simulate_readings")
        self.stdout.write(
            self.style.SUCCESS(
                f"TELDEM sensor simulator running every {interval}s. Press Ctrl+C to stop."
            )
        )
        job()  # run once immediately so the demo has fresh data right away
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write(self.style.WARNING("Scheduler stopped."))
