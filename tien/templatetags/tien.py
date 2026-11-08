from django import template
from django.utils.safestring import mark_safe

from tien.content import ICONS

register = template.Library()


@register.simple_tag
def icon(key):
    return mark_safe('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                     f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(key, "")}</svg>')


@register.filter
def numword(n):
    """4 -> 'Four' for headings; falls back to digits above twenty."""
    words = "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen Fifteen Sixteen " \
            "Seventeen Eighteen Nineteen Twenty".split()
    return words[n] if isinstance(n, int) and 0 <= n < len(words) else str(n)
