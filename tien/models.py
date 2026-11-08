"""Data model reconstructed from tienghana.org, extended for the immersive front-end."""
from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify

from .choices import (CONTACT_TOPICS, DESIGNATIONS, INSTITUTION_TYPES, MAP_CATEGORIES, MENTOR_EXPERIENCE,
                      NEWS_CATEGORIES, PARTNER_INTERESTS, PARTNER_TYPES, REGIONS, ROLLOUT_WAVES, YEAR_OF_STUDY)

# Ghana numbers (0XX… or +233…). Mentors may be abroad, so any E.164 number is also accepted.
phone_validator = RegexValidator(
    r"^(\+233[235]\d{8}|0[235]\d{8}|\+[1-9]\d{7,14})$",
    "Enter a valid phone number, e.g. 024 123 4567 or +233 24 123 4567.",
)


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Consented(models.Model):
    """Every public form records consent to processing under the Data Protection Act, 2012 (Act 843)."""
    consent_given = models.BooleanField(default=False)

    class Meta:
        abstract = True


class InstitutionQuerySet(models.QuerySet):
    def in_network(self):
        """Campuses shown publicly: the proposed rollout plus any institution switched on in admin."""
        return self.filter(models.Q(rollout_wave__isnull=False) | models.Q(is_member=True))


class Institution(TimeStamped):
    name = models.CharField(max_length=200, unique=True)
    short_name = models.CharField(max_length=30, blank=True)
    institution_type = models.CharField(max_length=40, choices=INSTITUTION_TYPES)
    map_category = models.CharField(max_length=20, choices=MAP_CATEGORIES, default="university")
    region = models.CharField(max_length=30, choices=REGIONS, blank=True)
    city = models.CharField(max_length=80, blank=True)
    latitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    longitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    coordinates_estimated = models.BooleanField(default=False, help_text="Tick if the map position still needs checking.")
    rollout_wave = models.PositiveSmallIntegerField(choices=ROLLOUT_WAVES, null=True, blank=True,
                                                    help_text="Leave empty if not in the proposed chapter rollout.")
    is_member = models.BooleanField(default=False, help_text="Has a confirmed TIEN chapter.")
    logo = models.ImageField(upload_to="institutions/", blank=True)

    objects = InstitutionQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_pilot(self):
        return self.rollout_wave == 0

    @property
    def status_label(self):
        if self.rollout_wave == 0:
            return "Pilot"
        if self.rollout_wave is not None:
            return dict(ROLLOUT_WAVES)[self.rollout_wave].replace("Planned, ", "")
        return "Member"


class InstitutionChoiceMixin(models.Model):
    institution = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.SET_NULL)
    institution_other = models.CharField("Institution name", max_length=200, blank=True)

    class Meta:
        abstract = True

    @property
    def institution_display(self):
        return str(self.institution) if self.institution_id else self.institution_other


class StudentRegistration(TimeStamped, Consented, InstitutionChoiceMixin):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=16, validators=[phone_validator])
    institution_type = models.CharField(max_length=40, choices=INSTITUTION_TYPES)
    program_of_study = models.CharField(max_length=150, blank=True)
    year_of_study = models.CharField(max_length=20, choices=YEAR_OF_STUDY, blank=True)
    area_of_interest = models.CharField(max_length=150, blank=True)
    interests = models.JSONField(default=list, blank=True)
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name


class InstitutionRegistration(TimeStamped, Consented, InstitutionChoiceMixin):
    institution_type = models.CharField(max_length=40, choices=INSTITUTION_TYPES)
    region = models.CharField(max_length=30, choices=REGIONS)
    contact_person = models.CharField(max_length=150)
    contact_role = models.CharField(max_length=120, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=16, validators=[phone_validator])
    student_numbers = models.PositiveIntegerField(null=True, blank=True)
    interests = models.JSONField(default=list, blank=True)
    message = models.TextField(blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.institution_display} ({self.contact_person})"


class ContactMessage(TimeStamped, Consented):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    topic = models.CharField(max_length=40, choices=CONTACT_TOPICS, default="General question")
    message = models.TextField()
    handled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.topic} from {self.name}"


class PartnerInquiry(TimeStamped, Consented):
    contact_name = models.CharField("Your name", max_length=150)
    organization = models.CharField("Organisation", max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=16, blank=True, validators=[phone_validator])
    interest = models.CharField("Interested in", max_length=60, choices=PARTNER_INTERESTS, default="Anchor partnership")
    partner_type = models.CharField(max_length=30, choices=PARTNER_TYPES, blank=True)
    message = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "partner inquiries"

    def __str__(self):
        return self.organization


class Subscriber(TimeStamped, Consented):
    email = models.EmailField(unique=True)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.email


class Person(TimeStamped):
    GROUPS = [("leadership", "Leadership"), ("advisory", "Advisory Board")]
    group = models.CharField(max_length=20, choices=GROUPS)
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="people/", blank=True)
    linkedin = models.URLField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["group", "order"]
        verbose_name_plural = "people"

    def __str__(self):
        return self.name


class Program(TimeStamped):
    KINDS = [("program", "Program"), ("opportunity", "Opportunity")]
    JOIN_ROLES = [("student", "Student"), ("mentor", "Mentor"), ("ambassador", "Ambassador")]
    ICONS = [(k, k) for k in ("bulb", "star", "chat", "flask", "hub", "mega", "mentor", "coin", "brief")]
    kind = models.CharField(max_length=20, choices=KINDS)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=150)
    summary = models.CharField(max_length=300)
    who = models.CharField("Who it is for", max_length=200, blank=True)
    format = models.CharField(max_length=200, blank=True)
    benefits = models.CharField("What you get", max_length=200, blank=True)
    body = models.TextField(blank=True)
    icon = models.CharField(max_length=20, choices=ICONS, default="bulb")
    join_role = models.CharField(max_length=20, choices=JOIN_ROLES, default="student")
    applications_open = models.BooleanField(default=True)
    deadline = models.DateField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["kind", "order"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/{'programs' if self.kind == 'program' else 'opportunities'}/{self.slug}/"


class Application(TimeStamped, Consented, InstitutionChoiceMixin):
    """Mentor and ambassador sign-ups from the join wizard, and program applications."""
    ROLES = [("mentor", "Mentor"), ("ambassador", "Ambassador"), ("student", "Student")]
    STATUS = [(s, s.title()) for s in ("submitted", "shortlisted", "accepted", "rejected")]
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="applications")
    role = models.CharField(max_length=20, choices=ROLES)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=16, validators=[phone_validator])
    student = models.ForeignKey(StudentRegistration, null=True, blank=True, on_delete=models.SET_NULL)
    organisation = models.CharField(max_length=200, blank=True)
    expertise = models.CharField(max_length=200, blank=True)
    years_experience = models.CharField(max_length=20, choices=MENTOR_EXPERIENCE, blank=True)
    motivation = models.TextField(blank=True)
    interests = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="submitted")

    def __str__(self):
        return f"{self.full_name}: {self.program}"


class Event(TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    is_online = models.BooleanField(default=False)
    description = models.TextField()
    cover = models.ImageField(upload_to="events/", blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title


class RSVP(TimeStamped, Consented):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    name = models.CharField(max_length=150)
    email = models.EmailField()

    class Meta:
        unique_together = ("event", "email")


class Article(TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=20, choices=NEWS_CATEGORIES)
    excerpt = models.CharField(max_length=300)
    body = models.TextField()
    cover = models.ImageField(upload_to="news/", blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.title)[:50]
        super().save(*args, **kwargs)


class Payment(TimeStamped, Consented):
    STATUS = [("pending", "Pending"), ("success", "Success"), ("failed", "Failed")]
    reference = models.CharField(max_length=64, unique=True)
    email = models.EmailField()
    amount_pesewas = models.PositiveIntegerField()  # Paystack works in the minor unit
    designation = models.CharField(max_length=20, choices=DESIGNATIONS, default="general")
    institution = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Set when the gift is for a campus chapter.")
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    raw_event = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.reference} GHS {self.amount_cedis} ({self.status})"

    @property
    def amount_cedis(self):
        return self.amount_pesewas / 100
