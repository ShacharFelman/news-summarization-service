from django.core.management.base import BaseCommand
from celery import current_app
from fetchers.tasks import test_task


class Command(BaseCommand):
    help = 'Check Celery worker and beat status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking Celery status...'))

        # Check if Celery workers are running
        try:
            inspect = current_app.control.inspect()
            stats = inspect.stats()

            if stats:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Found {len(stats)} active Celery worker(s)')
                )
                for worker, info in stats.items():
                    self.stdout.write(f'  - {worker}: {info.get("pool", {}).get("max-concurrency", "N/A")} processes')
            else:
                self.stdout.write(
                    self.style.ERROR('✗ No active Celery workers found')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error checking workers: {e}')
            )

        # Test task execution
        self.stdout.write('\nTesting task execution...')
        try:
            result = test_task.delay()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Test task queued with ID: {result.task_id}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error queuing test task: {e}')
            )

        # Check scheduled tasks
        self.stdout.write('\nChecking scheduled tasks...')
        try:
            scheduled = inspect.scheduled()
            if scheduled:
                for worker, tasks in scheduled.items():
                    self.stdout.write(f'  - {worker}: {len(tasks)} scheduled tasks')
            else:
                self.stdout.write('  - No scheduled tasks found')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not check scheduled tasks: {e}')
            )