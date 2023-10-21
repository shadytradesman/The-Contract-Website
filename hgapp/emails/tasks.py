from celery import shared_task
from django.core.mail import send_mail

@shared_task(name="send_email")
def send_email(subject, message, from_email, recipient_list, fail_silently, html_message):
    return send_mail(subject, message, from_email, recipient_list, fail_silently=fail_silently, html_message=html_message)
