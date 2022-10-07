from django.db.models.signals import pre_delete
from django.dispatch import receiver
from games.models import Game_Invite, NotifyGameInvitee
from django.template.loader import render_to_string
from django.core.mail import send_mail
from postman.api import pm_write
from django.urls import reverse
from django.utils.safestring import SafeText
from account.models import EmailAddress
from django.conf import settings

import logging

logger = logging.getLogger("app." + __name__)

from_email = settings.DEFAULT_FROM_EMAIL

@receiver(NotifyGameInvitee)
def notify_game_invitee(sender, **kwargs):
    print("game invitee notified")
    invite = kwargs["game_invite"]
    request = kwargs["request"]
    # This string is considered "safe" only because the markdown renderer will escape malicious HTML and scripts.
    game_url = request.build_absolute_uri(reverse("games:games_view_game", args=[invite.relevant_game.id]))
    message_body = SafeText('###{0} has invited you to an upcoming Game in {1}\n\n{2}\n\n [Click Here]({3}) to respond.'
                            .format(invite.relevant_game.creator.get_username(),
                                    invite.relevant_game.cell.name,
                                    invite.invite_text,
                                    game_url,
                                    ))
    pm_write(sender=invite.relevant_game.creator,
             recipient=invite.invited_player,
             subject=invite.relevant_game.creator.get_username() + " has invited you to join " + invite.relevant_game.title,
             body=message_body,
             skip_notification=True,
             auto_archive=True,
             auto_delete=False,
             auto_moderators=None)
    if invite.invited_player.profile.contract_invitations:
        print("game invitee will be emailed")
        user = invite.invited_player
        email = EmailAddress.objects.get_primary(user)
        is_verified = email and email.verified
        if is_verified:
            send_email_for_game_invite(email, invite, game_url)


def send_email_for_game_invite(email, game_invite, game_url):
    logger.info("sending game invite email to {}".format(email.email))
    invited_player = game_invite.invited_player
    gm = game_invite.relevant_game.creator
    context = {
        'invited_player': invited_player,
        'gm': gm,
        'game_url': game_url,
        'invite_text': game_invite.invite_text,
        'game': game_invite.relevant_game,
    }
    subject = "A Harbinger in {} calls. . .".format(game_invite.relevant_game.cell.name)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    html_message = render_to_string("emails/game_email.html", context)
    message = render_to_string('emails/game_email.txt', context)

    logger.info(message)
    send_mail(subject, message, from_email, [email.email], fail_silently=False, html_message=html_message)
