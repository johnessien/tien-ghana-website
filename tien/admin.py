import csv
from datetime import timedelta

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from . import models
from .roles import SUBMISSION_MODELS

admin.site.site_header = "TIEN Ghana Secretariat"
admin.site.site_title = "TIEN Ghana admin"
admin.site.index_title = "Dashboard"
admin.site.index_template = "admin/tien_index.html"


# ---------------------------------------------------------------- submissions inbox on the dashboard
_original_index = admin.site.index


def _inbox(request):
    """One row per submission type the person may see: total, new this week, and still to deal with."""
    week_ago = timezone.now() - timedelta(days=7)
    rows = []
    for model, todo_filter, todo_label in SUBMISSION_MODELS:
        opts = model._meta
        if not request.user.has_perm(f"{opts.app_label}.view_{opts.model_name}"):
            continue
        qs = model.objects.all()
        url = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
        todo = qs.filter(**todo_filter).count() if todo_filter else None
        rows.append({
            "name": opts.verbose_name_plural.capitalize(), "url": url,
            "total": qs.count(), "new": qs.filter(created_at__gte=week_ago).count(),
            "todo": todo, "todo_label": todo_label,
            "todo_url": url + "?" + "&".join(f"{k}__exact={_qs_value(v)}" for k, v in todo_filter.items()) if todo_filter else url,
        })
    return rows


def _qs_value(v):
    return {True: "1", False: "0"}.get(v, v)


def _index(request, extra_context=None):
    return _original_index(request, extra_context={"inbox": _inbox(request), **(extra_context or {})})


admin.site.index = _index


# ---------------------------------------------------------------- CSV download
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _cell(value):
    """Plain text for spreadsheets. Text that a spreadsheet would run as a formula is prefixed with '."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(v) for v in value)
    value = str(value)
    return "'" + value if value.startswith(_FORMULA_START) else value


@admin.action(description="Download selected as CSV (spreadsheet)", permissions=["export"])
def export_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    fields = [f for f in opts.concrete_fields]
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    stamp = timezone.localtime().strftime("%Y-%m-%d")
    response["Content-Disposition"] = f'attachment; filename="tien-{opts.model_name}-{stamp}.csv"'
    response.write("﻿")  # so Excel opens accented names correctly
    writer = csv.writer(response)
    writer.writerow([str(f.verbose_name).capitalize() for f in fields])
    for obj in queryset.order_by("created_at"):
        row = []
        for f in fields:
            if f.choices:
                row.append(_cell(getattr(obj, f"get_{f.name}_display")()))
            elif f.is_relation:
                row.append(_cell(getattr(obj, f.name)))
            else:
                row.append(_cell(getattr(obj, f.attname)))
        writer.writerow(row)
    return response


class SubmissionAdmin(admin.ModelAdmin):
    """Shared set-up for everything visitors send in through the site's forms.

    Newest first, searchable, filterable by date. Full-control accounts (superusers) can edit, delete and download.
    Reviewers (staff in the "Submissions reviewers" group) can read everything and only update the
    `reviewer_editable` fields, such as "handled" or an application's status. They can never delete or download."""
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50
    actions = [export_csv]
    reviewer_editable = ()

    def has_export_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ("created_at", "updated_at")
        return [f.name for f in self.model._meta.concrete_fields
                if f.name not in self.reviewer_editable and f.name != "id"]

    def has_add_permission(self, request):
        # Submissions come from the website's forms, not from the admin.
        return False


@admin.register(models.Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "region", "map_category", "rollout_wave", "is_member", "coordinates_estimated")
    list_filter = ("rollout_wave", "is_member", "map_category", "region", "coordinates_estimated")
    list_editable = ("rollout_wave", "is_member")
    search_fields = ("name", "short_name", "city")


@admin.register(models.StudentRegistration)
class StudentAdmin(SubmissionAdmin):
    list_display = ("full_name", "email", "phone", "institution_name", "year_of_study", "created_at")
    list_filter = ("institution_type", "year_of_study", "email_verified", "institution__region")
    search_fields = ("full_name", "email", "phone", "institution__name", "institution_other", "program_of_study")
    list_select_related = ("institution",)

    @admin.display(description="Institution", ordering="institution__name")
    def institution_name(self, obj):
        return obj.institution_display


@admin.register(models.InstitutionRegistration)
class InstitutionRegistrationAdmin(SubmissionAdmin):
    list_display = ("institution_name", "contact_person", "contact_email", "contact_phone", "region", "approved",
                    "created_at")
    list_filter = ("approved", "region", "institution_type")
    search_fields = ("institution__name", "institution_other", "contact_person", "contact_email")
    list_editable = ("approved",)
    list_select_related = ("institution",)
    reviewer_editable = ("approved",)

    @admin.display(description="Institution", ordering="institution__name")
    def institution_name(self, obj):
        return obj.institution_display


@admin.register(models.Application)
class ApplicationAdmin(SubmissionAdmin):
    list_display = ("full_name", "role", "program", "email", "phone", "status", "created_at")
    list_filter = ("status", "role", "program")
    search_fields = ("full_name", "email", "phone", "organisation", "expertise")
    list_editable = ("status",)
    list_select_related = ("program",)
    reviewer_editable = ("status",)


@admin.register(models.ContactMessage)
class ContactMessageAdmin(SubmissionAdmin):
    list_display = ("name", "email", "topic", "preview", "handled", "created_at")
    list_filter = ("handled", "topic")
    search_fields = ("name", "email", "message")
    list_editable = ("handled",)
    reviewer_editable = ("handled",)

    @admin.display(description="Message")
    def preview(self, obj):
        return obj.message if len(obj.message) <= 80 else obj.message[:77] + "..."


@admin.register(models.PartnerInquiry)
class PartnerInquiryAdmin(SubmissionAdmin):
    list_display = ("organization", "contact_name", "email", "phone", "interest", "partner_type", "created_at")
    list_filter = ("interest", "partner_type")
    search_fields = ("organization", "contact_name", "email", "message")


@admin.register(models.Subscriber)
class SubscriberAdmin(SubmissionAdmin):
    list_display = ("email", "confirmed", "created_at")
    list_filter = ("confirmed",)
    search_fields = ("email",)


@admin.register(models.RSVP)
class RSVPAdmin(SubmissionAdmin):
    list_display = ("name", "email", "event", "created_at")
    list_filter = ("event",)
    search_fields = ("name", "email", "event__title")
    list_select_related = ("event",)


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "email", "amount_cedis", "designation", "institution", "status", "created_at")
    list_filter = ("status", "designation")
    readonly_fields = ("raw_event",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


for m in (models.Person, models.Program, models.Event, models.Article):
    admin.site.register(m)
