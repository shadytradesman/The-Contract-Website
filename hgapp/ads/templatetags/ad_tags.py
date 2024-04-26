from django import template
from random import randint

from ..models import FakeAd

register = template.Library()

@register.inclusion_tag('ads/tags/view.html')
def render_fake_ad(user, counter=1):
    if user.is_authenticated and user.profile.hide_fake_ads:
        return {
            "empty": True
        }
    ad = FakeAd.objects.order_by("?").first()
    if ad is None:
        return {
            "empty": True
        }
    if hasattr(ad, "picture") and ad.picture is not None:
        is_vertical = ad.picture_height > ad.picture_width
    else:
        is_vertical = False
    return {
        "ad": ad,
        "counter": counter,
        "show_edit": user.is_authenticated and user.is_superuser,
        "is_vertical": is_vertical
    }
