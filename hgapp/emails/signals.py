from django.dispatch import receiver
from games.models import Game_Invite, NotifyGameInvitee, GameChangeStartTime, GameEnded
from django.conf import settings
from django_ses.signals import bounce_received
from emails.tasks import start_time_change_notifications, game_ended_notifications, game_invite_notification

from .models import BouncedEmail


import logging

logger = logging.getLogger("app." + __name__)

from_email = settings.DEFAULT_FROM_EMAIL

NOTIF_VAR_UPCOMING = "upcoming"
NOTIF_VAR_FINISHED = "finished"


@receiver(GameChangeStartTime)
def notify_changed_start(**kwargs):
    game = kwargs["game"]
    request = kwargs["request"]
    uri_prefix = request.build_absolute_uri('/')
    start_time_change_notifications.delay(game.pk, uri_prefix)


@receiver(GameEnded)
def notify_game_ended(**kwargs):
    game = kwargs["game"]
    request = kwargs["request"]
    uri_prefix = request.build_absolute_uri('/')
    game_ended_notifications.delay(game.pk, uri_prefix)


@receiver(NotifyGameInvitee)
def notify_game_invitee(sender, **kwargs):
    invite = kwargs["game_invite"]
    request = kwargs["request"]
    uri_prefix = request.build_absolute_uri('/')
    game_invite_notification.delay(invite.pk, uri_prefix)


@receiver(bounce_received)
def bounce_handler(sender, mail_obj, bounce_obj, raw_message, *args, **kwargs):
    recipient_list = mail_obj['destination']
    for recipient in recipient_list:
        logger.info("Email bounced: {}".format(recipient))
        BouncedEmail.objects.create(email=recipient)
