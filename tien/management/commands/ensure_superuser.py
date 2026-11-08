"""Create the admin account from environment variables, once.

    DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD

Run on every deploy by build.sh. If the account already exists nothing is changed (the password is never
overwritten, so changing it in the admin later is safe). If the variables are missing it skips quietly."""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the admin account from DJANGO_SUPERUSER_* environment variables if it does not exist"

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not (username and password):
            self.stdout.write("ensure_superuser: DJANGO_SUPERUSER_USERNAME/PASSWORD not set; skipping.")
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"ensure_superuser: admin account '{username}' already exists; left unchanged.")
            return
        user = User(username=username, email=email)
        try:
            validate_password(password, user)
        except ValidationError as e:
            raise CommandError("DJANGO_SUPERUSER_PASSWORD is too weak: " + " ".join(e.messages) +
                               " Choose a longer password in the Render dashboard (Environment) and redeploy.")
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"ensure_superuser: created admin account '{username}'."))
