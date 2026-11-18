from django.apps import AppConfig
from django.db.models.signals import post_migrate


class TienConfig(AppConfig):
    name = "tien"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Connected after django.contrib.auth's own handler, so this app's permissions already exist when it runs.
        post_migrate.connect(_after_migrate, sender=self, dispatch_uid="tien_reviewer_group")


def _after_migrate(sender, **kwargs):
    from .roles import ensure_reviewer_group
    ensure_reviewer_group()
