"""Header mega menu, drawer and footer, built from the database so empty sections stay hidden."""
from django.urls import reverse
from django.utils import timezone

from . import models


def navigation(request):
    has_news = models.Article.objects.filter(published_at__lte=timezone.now()).exists() or \
        models.Event.objects.filter(starts_at__gte=timezone.now()).exists()
    has_leaders = models.Person.objects.filter(group="leadership").exists()
    has_advisers = models.Person.objects.filter(group="advisory").exists()

    about = [{"label": "About TIEN Ghana", "desc": "Vision, mission and values", "url": reverse("tien:about")},
             {"label": "How we are organised", "desc": "Board, advisers, secretariat and chapters",
              "url": reverse("tien:about") + "#governance"}]
    if has_leaders:
        about.append({"label": "Leadership", "desc": "The team running TIEN Ghana", "url": reverse("tien:leadership")})
    if has_advisers:
        about.append({"label": "Advisory Board", "desc": "Industry, academic and alumni advisers",
                      "url": reverse("tien:advisory_board")})
    if has_news:
        about.append({"label": "News and events", "desc": "Tertiary Times and what is coming up", "url": reverse("tien:news")})

    def items(kind):
        return [{"label": p.title, "desc": p.who if kind == "opportunity" else p.summary.split(",")[0].split(" and ")[0],
                 "url": p.get_absolute_url()} for p in models.Program.objects.filter(kind=kind)]

    progs, opps = items("program"), items("opportunity")
    nav = [{"key": "about", "label": "About", "url": reverse("tien:about"), "children": about}]
    if progs:
        nav.append({"key": "programs", "label": "Programs", "url": reverse("tien:programs"),
                    "children": [{"label": "All programs", "desc": "Overview and sector tracks",
                                  "url": reverse("tien:programs")}] + progs})
    if opps:
        nav.append({"key": "opportunities", "label": "Opportunities", "url": reverse("tien:opportunities"),
                    "children": [{"label": "All opportunities", "desc": "Lead, learn, fund or get placed",
                                  "url": reverse("tien:opportunities")}] + opps})
    nav += [{"key": "network", "label": "Network", "url": reverse("tien:network")},
            {"key": "partners", "label": "Partners", "url": reverse("tien:partners")},
            {"key": "contact", "label": "Contact", "url": reverse("tien:contact")}]

    drawer = [{"key": "home", "label": "Home", "url": reverse("tien:home")}] + \
        [{"key": n["key"], "label": n["label"], "url": n["url"]} for n in nav]
    if has_news:
        drawer.insert(-1, {"key": "news", "label": "News and events", "url": reverse("tien:news")})
    drawer.append({"key": "donate", "label": "Donate", "url": reverse("tien:donate")})

    explore = [{"label": "About", "url": reverse("tien:about")}] + \
        ([{"label": "Programs", "url": reverse("tien:programs")}] if progs else []) + \
        ([{"label": "Opportunities", "url": reverse("tien:opportunities")}] if opps else []) + \
        ([{"label": "News and events", "url": reverse("tien:news")}] if has_news else [])
    footer = [
        {"title": "Explore", "links": explore},
        {"title": "Network", "links": [{"label": "Campuses", "url": reverse("tien:network")},
                                        {"label": "Partners", "url": reverse("tien:partners")},
                                        {"label": "Donate", "url": reverse("tien:donate")},
                                        {"label": "Join", "url": reverse("tien:join")}]},
        {"title": "Connect", "links": [{"label": "Contact us", "url": reverse("tien:contact")},
                                        {"label": "Get updates", "url": reverse("tien:news") + "#subscribe"},
                                        {"label": "Privacy policy", "url": reverse("tien:privacy")}]},
    ]
    return {"nav": nav, "drawer": drawer, "footer_columns": footer,
            "contact_email": "tertiaryinnovationexcellence@gmail.com"}
