from django.db.models.signals import pre_delete
from django.dispatch import receiver
from games.models import Game_Invite, NotifyGameInvitee, GameChangeStartTime, GameEnded
from django.template.loader import render_to_string
from emails.tasks import send_email
from postman.api import pm_write
from django.urls import reverse
from django.utils.safestring import SafeText
from django.conf import settings

from notifications.models import Notification, CONTRACT_NOTIF, REWARD_NOTIF

import logging

logger = logging.getLogger("app." + __name__)

from_email = settings.DEFAULT_FROM_EMAIL

NOTIF_VAR_UPCOMING = "upcoming"
NOTIF_VAR_FINISHED = "finished"

@receiver(GameChangeStartTime)
def notify_changed_start(**kwargs):
    game = kwargs["game"]
    request = kwargs["request"]
    game_url = request.build_absolute_uri(reverse("games:games_view_game", args=[game.id]))
    for invite in game.game_invite_set.all():
        profile = invite.invited_player.profile
        Notification.objects.create(user=invite.invited_player,
                                    headline="Start time changed",
                                    content="New start time for " + invite.relevant_game.title,
                                    url=game_url,
                                    notif_type=CONTRACT_NOTIF)
        if profile.contract_updates:
            email = invite.invited_player.profile.get_confirmed_email()
            if email:
                send_email_for_game_time_update(email, invite, game_url)


@receiver(GameEnded)
def notify_game_ended(**kwargs):
    game = kwargs["game"]
    request = kwargs["request"]
    game_url = request.build_absolute_uri(reverse("games:games_view_game", args=[game.id]))
    players = []
    for invite in game.game_invite_set.all():
        players.append(invite.invited_player)
        profile = invite.invited_player.profile
        if profile.contract_updates and hasattr(invite, "attendance") and invite.attendance:
            if invite.attendance.attending_character:
                reward_url = request.build_absolute_uri(reverse("characters:characters_spend_reward", args=[invite.attendance.attending_character.id]))
            else:
                reward_url = request.build_absolute_uri(reverse("characters:characters_allocate_gm_exp"))
            if game.scenario.is_valid():
                scenario_url = request.build_absolute_uri(reverse("games:games_view_scenario", args=[game.scenario.id]))
            else:
                scenario_url = None
            attendance = invite.attendance
            character_name = attendance.attending_character.name if attendance.attending_character else "Your ringer"
            if not attendance.is_death():
                Notification.objects.create(user=invite.invited_player,
                                            headline="You've done well.",
                                            content="{} earned Rewards".format(character_name),
                                            url=reward_url,
                                            notif_type=REWARD_NOTIF,
                                            is_timeline=True,
                                            article=attendance)
                email = invite.invited_player.profile.get_confirmed_email()
                if email:
                    send_email_for_game_ended(email, invite, game_url, reward_url, scenario_url)

    # notify GM
    gm_exp_earned = game.is_introductory_game() or (game.achieves_golden_ratio() and game.cell.use_golden_ratio)
    gm_message = "One Improvement and 6 Exp" if gm_exp_earned else "One Improvement"
    Notification.objects.create(user=game.gm,
                                headline="You've earned Rewards for GMing",
                                content=gm_message,
                                url=reverse("games:games_allocate_improvement_generic"),
                                notif_type=REWARD_NOTIF)
    # Notify other Players in playgroup
    for membership in game.cell.get_unbanned_members():
        if membership.member_player:
            Notification.objects.create(user=membership.member_player,
                                        headline="Contract Completed in {}".format(game.cell.name),
                                        content=game.scenario.title,
                                        url=game_url,
                                        notif_type=CONTRACT_NOTIF,
                                        is_timeline=True,
                                        article=game,
                                        variety=NOTIF_VAR_FINISHED)


@receiver(NotifyGameInvitee)
def notify_game_invitee(sender, **kwargs):
    invite = kwargs["game_invite"]
    request = kwargs["request"]
    # This string is considered "safe" only because the markdown renderer will escape malicious HTML and scripts.
    game_url = request.build_absolute_uri(reverse("games:games_view_game", args=[invite.relevant_game.id]))
    Notification.objects.create(user=invite.invited_player,
                                headline="A Harbinger Calls. . .",
                                content="Upcoming Contract: " + invite.relevant_game.title,
                                url=game_url,
                                notif_type=CONTRACT_NOTIF,
                                is_timeline=True,
                                article=invite.relevant_game,
                                variety=NOTIF_VAR_UPCOMING)
    if invite.invited_player.profile.contract_invitations:
        email = invite.invited_player.profile.get_confirmed_email()
        if email:
            send_email_for_game_invite(email, invite, game_url)


def send_email_for_game_ended(email, game_invite, game_url, reward_url, scenario_url):
    logger.info("sending game ended email to {}".format(email.email))
    invited_player = game_invite.invited_player
    gm = game_invite.relevant_game.creator
    attendance = game_invite.attendance
    character_name = attendance.attending_character.name if attendance.attending_character else "an NPC Ringer"
    context = {
        'invited_player': invited_player,
        'gm': gm,
        'attendance': attendance,
        'character_name': character_name,
        'game_url': game_url,
        'reward_url': reward_url,
        'game': game_invite.relevant_game,
        'scenario_url': scenario_url,
    }
    if attendance.is_victory():
        subject = "{} was victorious, earning a Gift and Experience!".format(character_name)
    else:
        subject = "{} finalized their Contract, and you earned Experience!".format(gm.username)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    html_message = render_to_string("emails/game_end_email.html", context)
    message = render_to_string('emails/game_end_email.txt', context)

    send_email(subject, message, from_email, [email.email], fail_silently=False, html_message=html_message)


def send_email_for_game_time_update(email, game_invite, game_url):
    logger.info("sending game time update email to {}".format(email.email))
    invited_player = game_invite.invited_player
    gm = game_invite.relevant_game.creator
    context = {
        'invited_player': invited_player,
        'gm': gm,
        'game_url': game_url,
        'game': game_invite.relevant_game,
    }
    subject = "Start time changed for {}'s upcoming Contract".format(gm.username)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    html_message = render_to_string("emails/game_start_update_email.html", context)
    message = render_to_string('emails/game_start_update_email.txt', context)

    send_email(subject, message, from_email, [email.email], fail_silently=False, html_message=html_message)


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

    send_email(subject, message, from_email, [email.email], fail_silently=False, html_message=html_message)
