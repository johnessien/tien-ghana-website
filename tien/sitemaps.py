from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Article, Program


class StaticSitemap(Sitemap):
    changefreq = "monthly"

    def items(self):
        return ["home", "about", "programs", "opportunities", "network", "partners", "donate", "join",
                "contact", "news", "privacy"]

    def location(self, item):
        return reverse(f"tien:{item}")


class ProgramSitemap(Sitemap):
    def items(self):
        return Program.objects.all()


class ArticleSitemap(Sitemap):
    def items(self):
        return Article.objects.exclude(published_at=None)

    def location(self, obj):
        return reverse("tien:news_detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {"pages": StaticSitemap, "programs": ProgramSitemap, "news": ArticleSitemap}
