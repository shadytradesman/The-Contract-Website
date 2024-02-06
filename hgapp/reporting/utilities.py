import hashlib
from .models import ALLOWED_CONTENT_APPS, ALLOWED_CONTENT_MODELS


def ensure_content_type_is_reportable(content_type):
    if content_type.app_label not in ALLOWED_CONTENT_APPS:
        raise ValueError("You cannot report this type of content")
    if content_type.model not in ALLOWED_CONTENT_MODELS:
        raise ValueError("You cannot report this type of content")


def ensure_content_object_is_reportable(content_object):
    if not hasattr(content_object, "get_responsible_user"):
        raise ValueError("Passed object does not implement get_responsible_user")
    if not hasattr(content_object, "report_remove"):
        raise ValueError("Passed object does not implement report_remove")
    if not hasattr(content_object, "render_for_report"):
        raise ValueError("Passed object does not implement render_for_report")


def get_url_for_content(content, content_type=None):
    if hasattr(content, "get_absolute_url"):
        return content.get_absolute_url()
    else:
        if content_type is None:
            raise ValueError("Must pass content type if content object does not implement get_absolute_url")
        hash_str = "||app{}||model{}||pk{}||".format(content_type.app_label, content_type.model, content.pk)
        return "content{}".format(hashlib.sha224(hash_str.encode()).hexdigest())
