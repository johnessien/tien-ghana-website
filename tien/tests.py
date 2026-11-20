import hashlib
import hmac
import json
import re
from unittest import mock

from django.test import TestCase, override_settings

from . import models


def ok_consent(**extra):
    return {"consent_given": "on", "website": "", **extra}


class PagesTest(TestCase):
    PAGES = {"/": "home", "/about/": "about", "/programs/": "programs", "/opportunities/": "opportunities",
             "/network/": "network", "/partners/": "partners", "/donate/": "donate", "/join/": "join",
             "/contact/": "contact", "/news/": "news", "/privacy/": "privacy"}

    def test_every_page_sets_data_page_and_has_no_mailto_or_placeholders(self):
        for url, page in self.PAGES.items():
            html = self.client.get(url).content.decode()
            self.assertIn(f'<body data-page="{page}"', html, url)
            for bad in ("mailto:", "lh3.googleusercontent.com", "500 000 000", "partnerships@tienghana.org",
                        'href="https://maps.google.com"', "/payments/?amount"):
                self.assertNotIn(bad, html, f"{bad} on {url}")
            self.assertIn('id="world-data"', html)

    def test_story_only_on_home(self):
        self.assertIn('id="rail"', self.client.get("/").content.decode())
        self.assertNotIn('class="chapter"', self.client.get("/about/").content.decode())

    def test_stats_come_from_database(self):
        r = self.client.get("/")
        self.assertEqual(r.context["stats"]["wave_cumulative"], [4, 8, 12, 20])
        models.Institution.objects.filter(name="Ashesi University").update(rollout_wave=0)
        r = self.client.get("/network/")
        self.assertEqual(r.context["stats"]["pilots"], 5)
        self.assertContains(r, "starting with five pilot chapters")

    def test_network_pins_and_pilot_tags(self):
        r = self.client.get("/network/")
        data = json.loads(re.search(r'id="world-data" type="application/json">(.*?)</script>', r.content.decode()).group(1))
        self.assertEqual(len(data["campuses"]), 20)
        self.assertEqual(sum(1 for c in data["campuses"] if c["wave"] == 0), 4)
        self.assertEqual(r.content.decode().count('class="tag p">Pilot<'), 4)
        ug = next(c for c in data["campuses"] if c["name"] == "University of Ghana")
        self.assertEqual((ug["lat"], ug["lon"]), (5.65, -0.19))
        # an institution switched on in admin joins the map
        models.Institution.objects.filter(name="Valley View University").update(is_member=True)
        self.assertEqual(len(json.loads(re.search(r'id="world-data" type="application/json">(.*?)</script>',
                         self.client.get("/network/").content.decode()).group(1))["campuses"]), 21)

    def test_empty_sections_hidden_from_menu(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn(">News and events<", html.split("<main")[0])
        self.assertNotIn("/about/leadership/", html)
        models.Person.objects.create(group="leadership", name="A. Mensah", role="Executive Director")
        html = self.client.get("/").content.decode()
        self.assertIn("/about/leadership/", html)

    def test_reveal_only_hidden_with_js_class(self):
        css = open("static/css/site.css").read()
        self.assertIn(".js .reveal{opacity:0", css)
        self.assertNotRegex(css, r"(^|\n)\.reveal\{opacity:0")


class FormsTest(TestCase):
    def test_contact(self):
        r = self.client.post("/contact/", ok_consent(name="Kofi", email="k@example.com", topic="Media", message="Hi"))
        self.assertRedirects(r, "/contact/")
        m = models.ContactMessage.objects.get()
        self.assertTrue(m.consent_given)
        self.assertEqual(m.topic, "Media")

    def test_contact_errors_inline_and_consent_required(self):
        r = self.client.post("/contact/", {"name": "", "email": "bad", "message": ""})
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('id="email-err"', html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn("Please confirm you agree to the privacy policy.", html)
        self.assertEqual(models.ContactMessage.objects.count(), 0)

    def test_honeypot_blocks(self):
        r = self.client.post("/contact/", ok_consent(name="Bot", email="b@example.com", message="spam", website="x"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(models.ContactMessage.objects.count(), 0)

    def test_partner(self):
        r = self.client.post("/partners/", ok_consent(contact_name="Ama", organization="Gold Fields", email="a@gf.com",
                                                      phone="0241234567", interest="Sector track", message=""))
        self.assertRedirects(r, "/partners/#enquire", fetch_redirect_response=False)
        p = models.PartnerInquiry.objects.get()
        self.assertEqual((p.phone, p.interest, p.consent_given), ("+233241234567", "Sector track", True))

    def test_subscribe_and_duplicate(self):
        self.assertEqual(self.client.post("/subscribe/", ok_consent(email="Me@Example.com")).status_code, 302)
        self.assertEqual(self.client.post("/subscribe/", ok_consent(email="me@example.com")).status_code, 302)
        self.assertEqual(models.Subscriber.objects.get().email, "me@example.com")
        r = self.client.post("/subscribe/", {"email": "x@example.com"})  # no consent
        self.assertContains(r, "Please confirm you agree")
        self.assertEqual(models.Subscriber.objects.count(), 1)


class JoinWizardTest(TestCase):
    def base(self, role, **kw):
        return ok_consent(**{"role": role, "full_name": "Efua Owusu", "email": f"{role}@example.com",
                             "phone": "055 123 4567", **kw})

    def test_student_with_listed_institution(self):
        ug = models.Institution.objects.get(name="University of Ghana")
        r = self.client.post("/join/", self.base("student", institution=ug.pk, institution_type="university",
                                                 year_of_study="Year 2", interests=["Innovation Challenges", "Innovation Grants"]))
        self.assertRedirects(r, "/join/?done=1", fetch_redirect_response=False)
        s = models.StudentRegistration.objects.get()
        self.assertEqual((s.institution, s.phone, s.interests), (ug, "+233551234567", ["Innovation Challenges", "Innovation Grants"]))
        self.assertContains(self.client.get("/join/?done=1"), "Application received")

    def test_student_not_listed(self):
        r = self.client.post("/join/", self.base("student", institution="other", institution_other="Nursing Training College, Korle Bu",
                                                 institution_type="college_of_education"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(models.StudentRegistration.objects.get().institution_display, "Nursing Training College, Korle Bu")

    def test_student_missing_institution_reopens_step_1(self):
        r = self.client.post("/join/", self.base("student", institution_type="university"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-start-step="1"', status_code=200)
        self.assertContains(r, 'id="institution-err"', status_code=200)

    def test_missing_consent_reopens_review_step(self):
        ug = models.Institution.objects.get(name="University of Ghana")
        data = self.base("student", institution=ug.pk, institution_type="university")
        del data["consent_given"]
        self.assertContains(self.client.post("/join/", data), 'data-start-step="3"', status_code=200)

    def test_duplicate_student_email(self):
        ug = models.Institution.objects.get(name="University of Ghana")
        d = self.base("student", institution=ug.pk, institution_type="university")
        self.client.post("/join/", d)
        self.assertContains(self.client.post("/join/", d), "already registered", status_code=200)

    def test_institution(self):
        knust = models.Institution.objects.get(short_name="KNUST")
        r = self.client.post("/join/", self.base("institution", institution=knust.pk, institution_type="university",
                                                 region="ashanti", contact_role="Dean of Students", student_numbers="85000"))
        self.assertEqual(r.status_code, 302)
        i = models.InstitutionRegistration.objects.get()
        self.assertEqual((i.institution, i.contact_person, i.student_numbers), (knust, "Efua Owusu", 85000))

    def test_mentor_goes_to_mentorship_application(self):
        r = self.client.post("/join/", self.base("mentor", organisation="Newmont", expertise="Mining engineering",
                                                 years_experience="11 to 20", phone="+447700900123"))
        self.assertEqual(r.status_code, 302)
        a = models.Application.objects.get()
        self.assertEqual((a.program.slug, a.role, a.years_experience), ("mentorship", "mentor", "11 to 20"))

    def test_ambassador_goes_to_campus_ambassador_application(self):
        uds = models.Institution.objects.get(short_name="UDS")
        r = self.client.post("/join/", self.base("ambassador", institution=uds.pk, institution_type="university",
                                                 motivation="I run the engineering society."))
        self.assertEqual(r.status_code, 302)
        a = models.Application.objects.get()
        self.assertEqual((a.program.slug, a.institution), ("campus-ambassador", uds))

    def test_ambassador_needs_motivation(self):
        uds = models.Institution.objects.get(short_name="UDS")
        r = self.client.post("/join/", self.base("ambassador", institution=uds.pk, institution_type="university"))
        self.assertContains(r, 'id="motivation-err"', status_code=200)

    def test_prefill_from_apply_links(self):
        r = self.client.get("/join/?role=mentor&interest=Mentorship+Program")
        self.assertContains(r, 'value="mentor" id="role-mentor" checked')
        self.assertContains(r, 'value="Mentorship Program" id="int-6" checked')


@override_settings(PAYSTACK_SECRET_KEY="sk_test_dummy")
class DonateTest(TestCase):
    def fake_init(self, method, path, **kw):
        self.sent = kw.get("json")
        resp = mock.Mock(); resp.raise_for_status = lambda: None
        resp.json = lambda: {"status": True, "data": {"authorization_url": "https://checkout.paystack.com/abc123"}}
        return resp

    def test_preset_amount_posts_to_server_and_redirects_to_paystack(self):
        with mock.patch("tien.views.paystack_request", side_effect=self.fake_init):
            r = self.client.post("/donate/", ok_consent(preset="460", designation="general", email="d@example.com"))
        self.assertRedirects(r, "https://checkout.paystack.com/abc123", fetch_redirect_response=False)
        self.assertEqual((self.sent["amount"], self.sent["currency"]), (46000, "GHS"))
        self.assertEqual(models.Payment.objects.get().amount_pesewas, 46000)

    def test_custom_amount_and_campus_designation(self):
        umat = models.Institution.objects.get(short_name="UMaT")
        with mock.patch("tien.views.paystack_request", side_effect=self.fake_init):
            r = self.client.post("/donate/", ok_consent(preset="other", custom="1250.50", designation="chapter",
                                                        campus=umat.pk, email="d@example.com"))
        self.assertEqual(r.status_code, 302)
        p = models.Payment.objects.get()
        self.assertEqual((p.amount_pesewas, p.institution, p.designation), (125050, umat, "chapter"))
        self.assertIn("University of Mines and Technology", self.sent["metadata"]["designation"])

    def test_validation(self):
        r = self.client.post("/donate/", ok_consent(preset="other", custom="1", designation="chapter", email="d@example.com"))
        self.assertContains(r, 'id="custom-err"', status_code=200)
        self.assertContains(r, 'id="campus-err"', status_code=200)
        self.assertEqual(models.Payment.objects.count(), 0)

    def test_amount_in_url_is_ignored(self):
        self.assertContains(self.client.get("/donate/?amount=999999"), 'value="460"')
        self.assertNotContains(self.client.get("/donate/?amount=999999"), "999999")

    def test_paystack_down_shows_inline_error(self):
        with mock.patch("tien.views.paystack_request", side_effect=ConnectionError):
            r = self.client.post("/donate/", ok_consent(preset="50", designation="general", email="d@example.com"))
        self.assertContains(r, "couldn&#x27;t reach the payment provider", status_code=200)
        self.assertEqual(models.Payment.objects.get().status, "failed")

    def test_callback_verifies_amount(self):
        p = models.Payment.objects.create(reference="TIEN-1", email="d@example.com", amount_pesewas=46000, consent_given=True)
        verify = mock.Mock(); verify.json = lambda: {"data": {"status": "success", "amount": 46000, "currency": "GHS"}}
        with mock.patch("tien.views.paystack_request", return_value=verify):
            r = self.client.get("/payments/callback/?reference=TIEN-1")
        self.assertContains(r, "Thank you for your gift")
        self.assertContains(r, "1 student")
        p.refresh_from_db(); self.assertEqual(p.status, "success")

    def test_callback_rejects_wrong_amount(self):
        models.Payment.objects.create(reference="TIEN-2", email="d@example.com", amount_pesewas=46000)
        verify = mock.Mock(); verify.json = lambda: {"data": {"status": "success", "amount": 100, "currency": "GHS"}}
        with mock.patch("tien.views.paystack_request", return_value=verify):
            self.client.get("/payments/callback/?reference=TIEN-2")
        self.assertEqual(models.Payment.objects.get().status, "pending")

    def test_webhook_signature(self):
        models.Payment.objects.create(reference="TIEN-3", email="d@example.com", amount_pesewas=5000)
        body = json.dumps({"event": "charge.success", "data": {"reference": "TIEN-3", "amount": 5000}}).encode()
        self.assertEqual(self.client.post("/payments/webhook/paystack/", body, content_type="application/json",
                                          HTTP_X_PAYSTACK_SIGNATURE="nope").status_code, 400)
        sig = hmac.new(b"sk_test_dummy", body, hashlib.sha512).hexdigest()
        self.assertEqual(self.client.post("/payments/webhook/paystack/", body, content_type="application/json",
                                          HTTP_X_PAYSTACK_SIGNATURE=sig).status_code, 200)
        self.assertEqual(models.Payment.objects.get().status, "success")


@override_settings(PAYSTACK_SECRET_KEY="")
class GivingClosedTest(TestCase):
    def test_donate_page_offers_contact_form_without_paystack(self):
        r = self.client.get("/donate/")
        self.assertContains(r, "Online giving opens soon")
        self.assertContains(r, 'action="/contact/"')
        self.assertContains(r, '<option value="Donations" selected>')
        self.assertNotContains(r, 'id="donateForm"')

    def test_post_to_donate_never_contacts_paystack(self):
        with mock.patch("tien.views.paystack_request") as pay:
            r = self.client.post("/donate/", ok_consent(preset="460", designation="general", email="d@example.com"))
        pay.assert_not_called()
        self.assertContains(r, "Online giving opens soon")
        self.assertEqual(models.Payment.objects.count(), 0)

    def test_pledge_via_contact_form_returns_to_donate(self):
        r = self.client.post("/contact/", ok_consent(name="Esi", email="esi@example.com", topic="Donations",
                                                     message="I'd like to sponsor a chapter.", next="/donate/"))
        self.assertRedirects(r, "/donate/", fetch_redirect_response=False)
        self.assertEqual(models.ContactMessage.objects.get().topic, "Donations")

    def test_contact_next_cannot_redirect_offsite(self):
        r = self.client.post("/contact/", ok_consent(name="X", email="x@example.com", topic="Media", message="m", next="//evil.example"))
        self.assertRedirects(r, "/contact/", fetch_redirect_response=False)
        r = self.client.post("/contact/", ok_consent(name="Y", email="y@example.com", topic="Media", message="m", next="/\\evil.example"))
        self.assertRedirects(r, "/contact/", fetch_redirect_response=False)

    def test_rest_of_site_works_without_paystack(self):
        for url in ("/", "/join/", "/network/", "/partners/", "/contact/", "/news/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)


class DeployTest(TestCase):
    def test_healthz(self):
        r = self.client.get("/healthz", HTTP_HOST="10.0.0.5:10000")  # internal host, not in ALLOWED_HOSTS
        self.assertEqual((r.status_code, r.content), (200, b"ok"))

    def test_ensure_superuser_creates_once_and_never_overwrites(self):
        from io import StringIO
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        env = {"DJANGO_SUPERUSER_USERNAME": "tienadmin", "DJANGO_SUPERUSER_EMAIL": "admin@example.com",
               "DJANGO_SUPERUSER_PASSWORD": "Kente-Loom-2026!"}
        with mock.patch.dict("os.environ", env):
            call_command("ensure_superuser", stdout=StringIO())
            user = get_user_model().objects.get(username="tienadmin")
            self.assertTrue(user.is_superuser and user.check_password("Kente-Loom-2026!"))
            with mock.patch.dict("os.environ", {"DJANGO_SUPERUSER_PASSWORD": "Different-Pass-99!"}):
                out = StringIO(); call_command("ensure_superuser", stdout=out)
            self.assertIn("already exists", out.getvalue())
            user.refresh_from_db(); self.assertTrue(user.check_password("Kente-Loom-2026!"))

    def test_ensure_superuser_skips_without_env_and_rejects_weak_password(self):
        from io import StringIO
        from django.core.management import CommandError, call_command
        with mock.patch.dict("os.environ", {}, clear=True):
            out = StringIO(); call_command("ensure_superuser", stdout=out)
            self.assertIn("skipping", out.getvalue())
        with mock.patch.dict("os.environ", {"DJANGO_SUPERUSER_USERNAME": "a", "DJANGO_SUPERUSER_PASSWORD": "12345678"}):
            with self.assertRaises(CommandError):
                call_command("ensure_superuser", stdout=StringIO())


class AdminAccessTest(TestCase):
    """The admin as the secretariat uses it: full-control accounts, read-only reviewers, the inbox and CSV download."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        from .roles import REVIEWER_GROUP
        User = get_user_model()
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "Kente-Loom-2026!")
        self.reviewer = User.objects.create_user("ama", "ama@example.com", "Kente-Loom-2026!", is_staff=True)
        self.reviewer.groups.add(Group.objects.get(name=REVIEWER_GROUP))
        self.msg = models.ContactMessage.objects.create(name="Kofi", email="k@example.com", message="=HYPERLINK(1)",
                                                        consent_given=True)
        models.Subscriber.objects.create(email="s@example.com", consent_given=True)

    def url(self, name, *args):
        from django.urls import reverse
        return reverse(f"admin:{name}", args=args)

    def test_reviewer_group_created_by_migrate_with_view_and_follow_up_rights_only(self):
        from django.contrib.auth.models import Group
        from .roles import REVIEWER_GROUP
        codes = set(Group.objects.get(name=REVIEWER_GROUP).permissions.values_list("codename", flat=True))
        for m in ("studentregistration", "institutionregistration", "application", "contactmessage",
                  "partnerinquiry", "subscriber", "rsvp"):
            self.assertIn(f"view_{m}", codes)
        self.assertIn("change_contactmessage", codes)
        self.assertFalse({c for c in codes if c.startswith(("delete_", "add_"))})
        self.assertNotIn("view_payment", codes)
        self.assertNotIn("change_user", codes)

    def test_dashboard_inbox_counts(self):
        self.client.force_login(self.boss)
        r = self.client.get(self.url("index"))
        self.assertContains(r, "Submissions from the website")
        self.assertContains(r, "1</strong> not handled")
        self.assertContains(r, "handled__exact=0")

    def test_reviewer_reads_and_marks_handled_but_cannot_edit_delete_or_download(self):
        self.client.force_login(self.reviewer)
        self.assertContains(self.client.get(self.url("index")), "Contact messages")
        self.assertEqual(self.client.get(self.url("tien_contactmessage_changelist")).status_code, 200)
        self.assertEqual(self.client.get(self.url("tien_payment_changelist")).status_code, 403)
        self.assertEqual(self.client.get(self.url("auth_user_changelist")).status_code, 403)
        change = self.url("tien_contactmessage_change", self.msg.pk)
        self.client.post(change, {"handled": "on", "name": "Changed", "email": "x@example.com", "message": "x"})
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.handled)
        self.assertEqual((self.msg.name, self.msg.email), ("Kofi", "k@example.com"))
        self.assertEqual(self.client.get(self.url("tien_contactmessage_delete", self.msg.pk)).status_code, 403)
        r = self.client.get(self.url("tien_contactmessage_changelist"))
        self.assertNotContains(r, "export_csv")

    def test_superuser_downloads_csv_safely(self):
        self.client.force_login(self.boss)
        r = self.client.post(self.url("tien_contactmessage_changelist"),
                             {"action": "export_csv", "_selected_action": [self.msg.pk]})
        self.assertEqual(r["Content-Type"], "text/csv; charset=utf-8")
        body = r.content.decode("utf-8-sig")
        self.assertIn("Kofi,k@example.com", body)
        self.assertIn("'=HYPERLINK(1)", body)  # spreadsheet formulas are neutralised

    def test_submissions_cannot_be_added_from_admin(self):
        self.client.force_login(self.boss)
        self.assertEqual(self.client.get(self.url("tien_contactmessage_add")).status_code, 403)
        for name in ("studentregistration", "institutionregistration", "application", "contactmessage",
                     "partnerinquiry", "subscriber", "rsvp"):
            self.assertEqual(self.client.get(self.url(f"tien_{name}_changelist") + "?q=a").status_code, 200, name)
