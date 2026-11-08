from django.contrib import admin

from . import models


@admin.register(models.Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "region", "map_category", "rollout_wave", "is_member", "coordinates_estimated")
    list_filter = ("rollout_wave", "is_member", "map_category", "region", "coordinates_estimated")
    list_editable = ("rollout_wave", "is_member")
    search_fields = ("name", "short_name", "city")


@admin.register(models.StudentRegistration)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "institution", "institution_other", "year_of_study", "created_at")
    list_filter = ("institution_type", "year_of_study", "email_verified")
    search_fields = ("full_name", "email", "institution_other")


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "program", "email", "status", "created_at")
    list_filter = ("role", "program", "status")


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "email", "amount_cedis", "designation", "institution", "status", "created_at")
    list_filter = ("status", "designation")
    readonly_fields = ("raw_event",)


for m in (models.InstitutionRegistration, models.ContactMessage, models.PartnerInquiry, models.Subscriber,
          models.Person, models.Program, models.Event, models.RSVP, models.Article):
    admin.site.register(m)
