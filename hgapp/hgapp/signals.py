from django_ses.signals import bounce_received
from django.dispatch import receiver
from account import EmailAddress
import logging

logger = logging.getLogger("app." + __name__)


@receiver(bounce_received)
def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
    recipient_list = mail_obj['destination']
    logger.error(mail_obj)
    for recipient in recipient_list:
        bounced_addrs = EmailAddress.objects.filter(email=recipient).all()
        for bounced_addr in bounced_addrs:
            bounced_addr.verified = False
            bounced_addr.save()
