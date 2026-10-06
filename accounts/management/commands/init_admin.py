from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create a default admin user if none exists'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Admin username')
        parser.add_argument('--password', default='admin123', help='Admin password')
        parser.add_argument('--email', default='admin@example.com', help='Admin email')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists."))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' successfully created!"))
