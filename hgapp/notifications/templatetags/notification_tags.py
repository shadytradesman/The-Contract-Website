from django import template
from ..models import Notification


register = template.Library()

@register.inclusion_tag('tags/menu_icon.html')
def notif_menu_icon(user):
    return {
        "num_unread": Notification.get_num_unread_notifications_for_player(user),
    }

@register.inclusion_tag('tags/notif_list_item.html')
def render_notification(notif, is_unread):
    return {
        "notif": notif,
        "is_unread": is_unread,
    }

@register.inclusion_tag('tags/notif_timeline_item.html', takes_context=True)
def render_timeline_notif(context, notif):
    request = context["request"] if "request" in context else None
    header = notif.article.render_timeline_header(request.user)
    content = notif.article.render_timeline_display(request.user)
    if content is not None:
        return {
            "notif": notif,
            "header": header,
            "content": content,
            "blank": False
        }
    else:
        return {
            "blank": True
        }


