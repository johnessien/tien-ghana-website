"""Who can see what in the admin.

Full control: superusers (the owner and the IT lead). Everyone else who needs to read what visitors send in gets a
staff account in the "Submissions reviewers" group: read every submission, update only the follow-up fields
(handled, approved, application status), never delete, never download, never touch site content or users.

The group is created (or topped up) after every `migrate`, so it exists on Render after the next deploy."""
from django.apps import apps as global_apps

REVIEWER_GROUP = "Submissions reviewers"

# (model name, filter for "still to deal with", label for that count). Used for the group and the dashboard inbox.
_SUBMISSIONS = [
    ("StudentRegistration", {}, ""),
    ("InstitutionRegistration", {"approved": False}, "not approved"),
    ("Application", {"status": "submitted"}, "not reviewed"),
    ("ContactMessage", {"handled": False}, "not handled"),
    ("PartnerInquiry", {}, ""),
    ("Subscriber", {}, ""),
    ("RSVP", {}, ""),
]
# Models where reviewers may change the follow-up field (the admin limits them to that field).
_REVIEWER_CAN_CHANGE = {"InstitutionRegistration", "Application", "ContactMessage"}


class _Lazy:
    def __iter__(self):
        for name, todo, label in _SUBMISSIONS:
            yield global_apps.get_model("tien", name), todo, label


SUBMISSION_MODELS = _Lazy()


def ensure_reviewer_group(sender=None, apps=global_apps, **kwargs):
    """post_migrate hook: make sure the reviewer group exists with at least its standard permissions.
    Only adds permissions, so anything an admin added by hand is kept."""
    try:
        Group = apps.get_model("auth", "Group")
        Permission = apps.get_model("auth", "Permission")
    except LookupError:
        return
    wanted = []
    for name, _, _ in _SUBMISSIONS:
        model = name.lower()
        wanted.append(f"view_{model}")
        if name in _REVIEWER_CAN_CHANGE:
            wanted.append(f"change_{model}")
    perms = list(Permission.objects.filter(content_type__app_label="tien", codename__in=wanted))
    if len(perms) < len(wanted):
        return  # permissions not created yet (first migrate on an empty database); the next migrate fills them
    group, _ = Group.objects.get_or_create(name=REVIEWER_GROUP)
    group.permissions.add(*perms)
