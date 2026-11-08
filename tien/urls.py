"""Real URLs for every hash route in the immersive front-end, plus redirects from the live site's old paths."""
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.generic import RedirectView

from . import views
from .sitemaps import SITEMAPS

app_name = "tien"


def moved(url, keep_query=True):
    return RedirectView.as_view(url=url, permanent=True, query_string=keep_query)


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("about/leadership/", views.people, {"group": "leadership"}, name="leadership"),
    path("about/advisory-board/", views.people, {"group": "advisory"}, name="advisory_board"),
    path("programs/", views.program_list, {"kind": "program"}, name="programs"),
    path("programs/<slug:slug>/", views.program_detail, {"kind": "program"}, name="program_detail"),
    path("opportunities/", views.program_list, {"kind": "opportunity"}, name="opportunities"),
    path("opportunities/<slug:slug>/", views.program_detail, {"kind": "opportunity"}, name="opportunity_detail"),
    path("network/", views.network, name="network"),
    path("partners/", views.partners, name="partners"),
    path("donate/", views.donate, name="donate"),
    path("join/", views.join, name="join"),
    path("contact/", views.contact, name="contact"),
    path("news/", views.news, name="news"),
    path("news/<slug:slug>/", views.news_detail, name="news_detail"),
    path("events/<slug:slug>/", views.event_detail, name="event_detail"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("privacy/", views.privacy, name="privacy"),
    path("payments/callback/", views.paystack_callback, name="paystack_callback"),
    path("payments/webhook/paystack/", views.paystack_webhook, name="paystack_webhook"),
    path("robots.txt", views.robots),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    # old tienghana.org paths keep working
    path("about/vision-mission/", moved("/about/#vision")),
    path("about/core-values/", moved("/about/#values")),
    path("network/institutions/", moved("/network/")),
    path("network/community/", moved("/join/")),
    path("join/register/", moved("/join/?role=student")),
    path("join/register-institution/", moved("/join/?role=institution")),
    path("events/", moved("/news/")),
    path("payments/", moved("/donate/", keep_query=False)),  # never carry ?amount= over
]
