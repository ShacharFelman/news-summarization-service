from django.core.management.base import BaseCommand
from fetchers.tasks import fetch_articles_task


class Command(BaseCommand):
    help = 'Manually trigger the periodic article fetch task'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run the task asynchronously through Celery'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting article fetch...'))

        if options['async']:
            # Run through Celery
            result = fetch_articles_task.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Task queued with ID: {result.task_id}')
            )
        else:
            # Run synchronously
            result = fetch_articles_task()
            self.stdout.write(
                self.style.SUCCESS(f'Task completed: {result}')
            )