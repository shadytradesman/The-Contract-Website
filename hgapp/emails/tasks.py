from celery import shared_task
import datetime
from django.core.mail import send_mail
from collections import defaultdict
from django.template.loader import render_to_string
from django.urls import reverse
from notifications.models import Notification, CONTRACT_NOTIF, REWARD_NOTIF
from django.conf import settings
from games.models import Game, Game_Invite, Scenario
from django.utils import timezone

from .models import BouncedEmail

import logging

logger = logging.getLogger("app." + __name__)

from_email = settings.DEFAULT_FROM_EMAIL

NOTIF_VAR_UPCOMING = "upcoming"
NOTIF_VAR_FINISHED = "finished"

@shared_task(name="campaign_exchange")
def campaign_exchange():
    scenarios = Scenario.objects.filter(num_words__gt=1000, is_on_exchange=False, times_run__gt=0).order_by("creator").all()
    scenarios_by_creator = defaultdict(list)
    for scenario in scenarios:
        if scenario.can_submit_to_exchange():
            scenarios_by_creator[scenario.creator].append(scenario)
    for creator, scenarios in scenarios_by_creator.items():
        recent_time = creator.profile.most_recent_game_time()
        is_active = False
        if recent_time is None or recent_time + datetime.timedelta(days=35) > timezone.now():
            is_active = True
        if not creator.profile.site_announcements:
            print("Not sending email to {} because their site announcements are disabled".format(creator.username))
            continue
        if len(scenarios) == 0:
            continue
        email = creator.profile.get_confirmed_email()
        if email is None:
            continue
        print("sending email to {}".format(creator.username))
        context = {
            'user': creator,
            'scenarios': scenarios,
        }
        if is_active:
            subject = "Support the Contract, donate a Scenario!"
            html_message = render_to_string("emails/campaigns/exchange_campaign_active.html", context)
            message = render_to_string('emails/campaigns/exchange_campaign_active.txt', context)
        else:
            subject = "Don’t let your Scenarios go extinct!"
            html_message = render_to_string("emails/campaigns/exchange_campaign.html", context)
            message = render_to_string('emails/campaigns/exchange_campaign.txt', context)

        send_email(subject, message, from_email, [email.email], fail_silently=False, html_message=html_message)


@shared_task(name="send_email")
def send_email(subject, message, from_email, recipient_list, fail_silently, html_message):
    valid_recipients = []
    for recipient in recipient_list:
        if BouncedEmail.objects.filter(email=recipient).first() is not None:
            logger.info("Not sending email to address because address has bounced: {}".format(str(recipient)))
            return
        else:
            valid_recipients.append(recipient)
    if valid_recipients:
        return send_mail(subject, message, from_email, valid_recipients, fail_silently=fail_silently, html_message=html_message)


@shared_task(name="game_invite_notification")
def game_invite_notification(invite_id, uri_prefix):
    invite = Game_Invite.objects.get(pk=invite_id)
    # This string is considered "safe" only because the markdown renderer will escape malicious HTML and scripts.
    game_url = "{}{}".format(uri_prefix, reverse("games:games_view_game", args=[invite.relevant_game.id])[1:])
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


@shared_task(name="start_time_change_notifications")
def start_time_change_notifications(game_id, uri_prefix):
    game = Game.objects.get(pk=game_id)
    game_url = "{}{}".format(uri_prefix, reverse("games:games_view_game", args=[game.id])[1:])
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


@shared_task(name="game_ended_notifications")
def game_ended_notifications(game_id, uri_prefix):
    game = Game.objects.get(pk=game_id)
    game_url = "{}{}".format(uri_prefix, reverse("games:games_view_game", args=[game.id])[1:])
    players = []
    for invite in game.game_invite_set.all():
        players.append(invite.invited_player)
        profile = invite.invited_player.profile
        if profile.contract_updates and hasattr(invite, "attendance") and invite.attendance:
            if invite.attendance.attending_character:
                reward_url = "{}{}".format(uri_prefix, 
                    reverse("characters:characters_spend_reward", args=[invite.attendance.attending_character.id])[1:])
            else:
                reward_url = "{}{}".format(uri_prefix, reverse("characters:characters_allocate_gm_exp")[1:])
            if game.scenario.is_valid():
                scenario_url = "{}{}".format(uri_prefix, reverse("games:games_view_scenario", args=[game.scenario.id])[1:])
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


def send_email_for_published_article(email, article, article_url):
    logger.info("sending email for published article to {}".format(email.email))
    context = {
        'article': article,
        'url': article_url,
    }
    subject = "Announcing {}".format(article.title)

    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    html_message = render_to_string("emails/article_email.html", context)
    message = render_to_string('emails/article_email.txt', context)

    send_email(subject, message, from_email, [email.email], fail_silently=False, html_message=html_message)
