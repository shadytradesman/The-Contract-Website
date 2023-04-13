from django import template

from ..models import FakeAd

register = template.Library()

@register.inclusion_tag('ads/tags/view.html')
def render_fake_ad(user):
    # if user.is_authenticated and user.profile.hide_fake_ads:
    if not user.is_authenticated or not user.profile.early_access_user or user.profile.hide_fake_ads:
        return {
            "empty": True
        }
    ad = FakeAd.objects.order_by("?").first()
    return {
        "ad": ad,
        "show_edit": user.is_authenticated and user.is_superuser,
    }
