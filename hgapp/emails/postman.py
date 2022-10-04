import logging

from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

from account.models import EmailAddress


logger = logging.getLogger("app." + __name__)

from_email = settings.DEFAULT_FROM_EMAIL


# This module is what postman uses to notify users. It ensures users receiving emails have the right prefs
# and also renders their content.
def send(users=None, label=None, extra_context=None):
    if label in ("postman_reply", "postman_message"):
        for user in users:
            email = EmailAddress.objects.get_primary(user)
            is_verified = email and email.verified
            if is_verified and hasattr(user, "profile") and user.profile and user.profile.direct_messages:
                _send_postman_email(email_addr=email, user=user, message=extra_context["pm_message"])


def _send_postman_email(email_addr, user, message):
    logger.info("sending postman email to {}".format(user))
    sender = message.obfuscated_sender
    view_url = "https://www.thecontractrpg.com" + message.get_absolute_url()
    context = {
        'message': message,
        'sender': sender,
        'view_url': view_url,
        'content_snip': message.body[0:250],
    }
    subject = "New direct message from {}".format(sender)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    html_message = render_to_string("emails/postman_email.html", context)
    message = render_to_string('emails/postman_email.txt', context)

    send_mail(subject, message, from_email, [email_addr.email], fail_silently=False, html_message=html_message)
