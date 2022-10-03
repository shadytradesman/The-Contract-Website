from django_ses.signals import bounce_received
from django.dispatch import receiver
import logging

logger = logging.getLogger("app." + __name__)


@receiver(bounce_received)
def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
    # you can then use the message ID and/or recipient_list(email address) to identify any problematic email messages that you have sent
    message_id = mail_obj['messageId']
    recipient_list = mail_obj['destination']
    print("This is bounce email object")
    print(mail_obj)
    logger.info(mail_obj)