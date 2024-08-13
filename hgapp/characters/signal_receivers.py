from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import transaction
from .tasks import recalculate_character_stats
from .models import ExperienceReward
from .signals import recalculate_stats

@receiver(recalculate_stats, dispatch_uid="recalculate_stats_id")
def recalculate_character_stats_receiver(sender, **kwargs):
    character_pk = kwargs["character_pk"]
    is_game = kwargs["is_game"]
    return transaction.on_commit(lambda: recalculate_character_stats.delay(character_pk, is_game))


@receiver(post_save, sender=ExperienceReward, dispatch_uid="exp_reward_recalculate_stats")
def recalculate_character_stats_exp_receiver(sender, instance, created, **kwargs):
    if instance and instance.rewarded_character:
        return transaction.on_commit(lambda: recalculate_character_stats.delay(instance.rewarded_character.pk, False))
