"""Server-rendered pages for the immersive front-end. Every number shown on the site
comes from site_stats() or another query, so the copy can't drift from the data."""
import hashlib
import hmac
import json
import logging
import secrets
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import content, forms, models
from .choices import COST_PER_STUDENT, DESIGNATIONS, DONATION_PRESETS, JOIN_INTERESTS, JOIN_ROLES, MAP_CATEGORIES, NEWS_CATEGORIES

log = logging.getLogger(__name__)
PAYSTACK = "https://api.paystack.co"


# ----------------------------------------------------------------- shared data
def site_stats():
    net = models.Institution.objects.in_network()
    waves = dict(net.exclude(rollout_wave=None).values_list("rollout_wave").annotate(n=Count("id")))
    cumulative, running = [], 0
    for w in range(4):
        running += waves.get(w, 0)
        cumulative.append(running)
    return {
        "campuses": net.count(),
        "rollout": cumulative[-1],
        "pilots": waves.get(0, 0),
        "wave_cumulative": cumulative,  # [Year 1, by Year 2, by Year 3, by Year 5]
        "regions": net.exclude(region="").values("region").distinct().count(),
        "students": models.StudentRegistration.objects.count(),
        "programs": models.Program.objects.filter(kind="program").count(),
    }


def campus_data():
    """Campus list for the 3D map and network page, in the shape world.js expects."""
    out = []
    for i in models.Institution.objects.in_network().exclude(latitude=None).order_by(
            "rollout_wave", "name"):
        out.append({"id": i.pk, "name": i.name, "city": i.city, "type": i.map_category,
                    "wave": i.rollout_wave if i.rollout_wave is not None else 9,
                    "lat": float(i.latitude), "lon": float(i.longitude), "status": i.status_label})
    return out


def render_page(request, template, page, ctx=None, status=200):
    ctx = ctx or {}
    ctx.setdefault("page", page)
    ctx.setdefault("stats", site_stats())
    ctx.setdefault("world", {"page": page, "campuses": campus_data(), "waves": ctx["stats"]["wave_cumulative"]})
    return render(request, template, ctx, status=status)


def _redirect_back(request, fallback):
    nxt = request.POST.get("next", "")
    safe = nxt.startswith("/") and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()},
                                                                   require_https=request.is_secure())
    return redirect(nxt if safe else fallback)


# ----------------------------------------------------------------- pages
def home(request):
    return render_page(request, "home.html", "home", {"national": content.NATIONAL,
                                                      "chapter_titles": content.CHAPTER_TITLES})


def about(request):
    return render_page(request, "about.html", "about", {
        "values": content.VALUES, "governance": content.GOVERNANCE,
        "has_people": models.Person.objects.exists()})


def people(request, group):
    qs = models.Person.objects.filter(group=group)
    if not qs.exists():
        return redirect(reverse("tien:about") + "#governance")
    return render_page(request, "about/people.html", "about", {"group": dict(models.Person.GROUPS)[group], "people": qs})


def program_list(request, kind):
    page = "programs" if kind == "program" else "opportunities"
    return render_page(request, f"{page}.html", page, {
        "items": models.Program.objects.filter(kind=kind), "tracks": content.TRACKS, "icons": content.ICONS})


def program_detail(request, slug, kind):
    item = get_object_or_404(models.Program, slug=slug, kind=kind)
    return render_page(request, "programs/detail.html", "programs" if kind == "program" else "opportunities",
                       {"item": item, "icons": content.ICONS})


def network(request):
    return render_page(request, "network.html", "network", {
        "campuses": models.Institution.objects.in_network().order_by("rollout_wave", "name"),
        "filters": [("all", "All"), ("pilot", "Pilot chapters")] + [
            (k, {"university": "Universities", "technical": "Technical", "specialist": "Engineering, energy and health",
                 "education": "Teacher education"}[k]) for k, _ in MAP_CATEGORIES]})


def partners(request):
    form = forms.PartnerInquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thank you. We'll send the partnership pack within two working days.")
        return redirect(reverse("tien:partners") + "#enquire")
    return render_page(request, "partners.html", "partners", {
        "form": form, "tiers": content.TIERS, "services": content.SERVICES,
        "accountability": content.ACCOUNTABILITY})


def contact(request):
    form = forms.ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Message sent. We'll reply within two working days.")
        return _redirect_back(request, reverse("tien:contact"))
    return render_page(request, "contact.html", "contact", {"form": form})


def news(request):
    articles = models.Article.objects.filter(published_at__lte=timezone.now())
    cat = request.GET.get("category")
    if cat in dict(NEWS_CATEGORIES):
        articles = articles.filter(category=cat)
    return render_page(request, "news.html", "news", {
        "articles": articles, "categories": NEWS_CATEGORIES, "active": cat,
        "events": models.Event.objects.filter(starts_at__gte=timezone.now())[:6],
        "subscribe_form": forms.SubscribeForm()})


def news_detail(request, slug):
    article = get_object_or_404(models.Article, slug=slug, published_at__lte=timezone.now())
    return render_page(request, "news_detail.html", "news", {"article": article})


def event_detail(request, slug):
    event = get_object_or_404(models.Event, slug=slug)
    return render_page(request, "event_detail.html", "news", {"event": event})


@require_POST
def subscribe(request):
    form = forms.SubscribeForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "You're subscribed. We'll keep you posted.")
        return _redirect_back(request, reverse("tien:news") + "#subscribe")
    if "email" in form.errors and models.Subscriber.objects.filter(email__iexact=request.POST.get("email", "")).exists():
        messages.success(request, "You're already subscribed. Thank you!")
        return _redirect_back(request, reverse("tien:news") + "#subscribe")
    return render_page(request, "news.html", "news", {
        "articles": models.Article.objects.filter(published_at__lte=timezone.now()), "categories": NEWS_CATEGORIES,
        "events": models.Event.objects.filter(starts_at__gte=timezone.now())[:6], "subscribe_form": form})


def privacy(request):
    return render_page(request, "privacy.html", "privacy")


# ----------------------------------------------------------------- join wizard
def join(request):
    if request.method == "POST":
        form = forms.JoinForm(request.POST)
        if form.is_valid():
            form.save()
            request.session["joined_as"] = form.cleaned_data["role"]
            return redirect(reverse("tien:join") + "?done=1")
    else:
        role = request.GET.get("role")
        interest = request.GET.get("interest")
        initial = {"role": role if role in dict((r[0], r[1]) for r in JOIN_ROLES) else "student"}
        if interest:
            initial["interests"] = [interest]
        form = forms.JoinForm(initial=initial)
    done_role = request.session.pop("joined_as", None) if request.GET.get("done") else None
    sel_inst = form["institution"].value()
    return render_page(request, "join.html", "join", {
        "form": form, "roles": JOIN_ROLES, "done_role": done_role,
        "done_label": dict((r[0], r[1]) for r in JOIN_ROLES).get(done_role, ""),
        "institutions": models.Institution.objects.all(), "selected_inst": "" if sel_inst is None else str(sel_inst),
        "interests": JOIN_INTERESTS, "selected_interests": form["interests"].value() or [],
        "selected_role": form["role"].value() or "student",
        "start_step": form.first_error_step if form.is_bound else (1 if request.GET.get("role") else 0)})


# ----------------------------------------------------------------- donate + Paystack
def paystack_request(method, path, **kwargs):
    """Single choke point for Paystack calls (also the seam the tests mock)."""
    return requests.request(method, f"{PAYSTACK}{path}", timeout=15,
                            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}, **kwargs)


def donate(request):
    if not settings.PAYSTACK_SECRET_KEY:
        # Online giving is switched off until Paystack keys are added: offer the contact form instead.
        return render_page(request, "donate.html", "donate", {
            "giving_closed": True, "cost_per_student": COST_PER_STUDENT,
            "contact_form": forms.ContactForm(initial={"topic": "Donations"})})
    form = forms.DonationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        amount = int((Decimal(d["amount"]) * 100).to_integral_value())
        ref = f"TIEN-{secrets.token_hex(8)}"
        campus = d["campus"] if d["designation"] == "chapter" else None
        payment = models.Payment.objects.create(reference=ref, email=d["email"].lower(), amount_pesewas=amount,
                                                designation=d["designation"], institution=campus, consent_given=True)
        label = dict(DESIGNATIONS)[d["designation"]] + (f": {campus}" if campus else "")
        try:
            if not settings.PAYSTACK_SECRET_KEY:
                raise RuntimeError("PAYSTACK_SECRET_KEY is not set")
            r = paystack_request("POST", "/transaction/initialize", json={
                "email": payment.email, "amount": amount, "currency": "GHS", "reference": ref,
                "callback_url": request.build_absolute_uri(reverse("tien:paystack_callback")),
                "metadata": {"designation": label, "custom_fields": [
                    {"display_name": "Designation", "variable_name": "designation", "value": label}]}})
            r.raise_for_status()
            return redirect(r.json()["data"]["authorization_url"])
        except Exception:  # network error, bad key, Paystack outage
            log.exception("Paystack initialise failed for %s", ref)
            payment.status = "failed"
            payment.save(update_fields=["status"])
            form.add_error(None, "We couldn't reach the payment provider. Your card has not been charged. "
                                 "Please try again in a few minutes.")
    return render_page(request, "donate.html", "donate", {
        "form": form, "presets": DONATION_PRESETS, "cost_per_student": COST_PER_STUDENT})


def paystack_callback(request):
    payment = get_object_or_404(models.Payment, reference=request.GET.get("reference", ""))
    if payment.status != "success":
        try:
            data = paystack_request("GET", f"/transaction/verify/{payment.reference}").json().get("data") or {}
            if data.get("status") == "success" and data.get("amount") == payment.amount_pesewas \
                    and data.get("currency", "GHS") == "GHS":
                payment.status = "success"
            elif data.get("status") in ("failed", "abandoned"):
                payment.status = "failed"
            payment.save(update_fields=["status"])
        except Exception:
            log.exception("Paystack verify failed for %s", payment.reference)
    return render_page(request, "receipt.html", "donate", {
        "payment": payment, "designation": dict(DESIGNATIONS)[payment.designation],
        "students_trained": int(payment.amount_cedis // COST_PER_STUDENT)})


@csrf_exempt
@require_POST
def paystack_webhook(request):
    sig = request.headers.get("x-paystack-signature", "")
    digest = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), request.body, hashlib.sha512).hexdigest()
    if not settings.PAYSTACK_SECRET_KEY or not hmac.compare_digest(sig, digest):
        return HttpResponseBadRequest("bad signature")
    event = json.loads(request.body)
    if event.get("event") == "charge.success":
        d = event["data"]
        models.Payment.objects.filter(reference=d.get("reference"), amount_pesewas=d.get("amount")).update(
            status="success", raw_event=event)
    return HttpResponse(status=200)


def robots(request):
    lines = ["User-agent: *", f"Disallow: /{settings.ADMIN_PATH}", "Disallow: /payments/",
             f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
