from celery import shared_task
from notifications.models import Notification, CONTRACTOR_NOTIF
from django.urls import reverse
from .models import Character


@shared_task(name="recalculate_character_stats")
def recalculate_character_stats(character_pk, is_game=False):
    character = Character.objects.get(pk=character_pk)
    original_status = character.status
    character.update_contractor_journal_stats()
    character.update_loss_count()
    character.update_victory_count()
    character.update_game_count()
    character.update_exp_earned()
    effective_victories = character.effective_victories()
    character.status = character.calculate_status(num_victories=effective_victories)
    character.save()
    if is_game and (character.status != original_status):
        for membership in character.cell.get_unbanned_members():
            Notification.objects.create(
                user=membership.member_player,
                headline="Contractor earned new Status",
                content="{} is now {}".format(character.name, character.get_contractor_status_display()),
                url=reverse('characters:characters_view', args=(character.id,)),
                notif_type=CONTRACTOR_NOTIF)
