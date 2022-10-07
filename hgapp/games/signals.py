
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Game_Attendance, Reward
from characters.signals import GrantAssetGift, VoidAssetGifts, AlterPortedRewards

# This is done as a signal instead of model override due to django doc recommendation
@receiver(pre_delete, sender=Game_Attendance, dispatch_uid="delete_attendance")
def set_default_character_view_permissions(sender, instance, **kwargs):
    if instance.attending_character:
        instance.attending_character.default_perms_char_and_powers_to_player(instance.relevant_game.creator)

@receiver(GrantAssetGift)
def grantAssetGift(sender, **kwargs):
    reward = Reward(rewarded_player=kwargs["character"].player,
                    rewarded_character=kwargs["character"],
                    is_improvement=False,
                    source_asset=kwargs["assetDetail"])
    reward.save()

@receiver(VoidAssetGifts)
def voidAssetGifts(sender, **kwargs):
    rewards = kwargs["character"].reward_set.filter(source_asset__isnull=False).all()
    for reward in rewards:
        reward.is_void = True
        reward.save()


@receiver(AlterPortedRewards)
def alterPortedRewards(sender, **kwargs):
    # voids or grants gifts based on the value of kwarg num_gifts
    character = kwargs["character"]
    num_gifts = kwargs["num_gifts"]
    num_improvements = kwargs["num_improvements"]
    if num_gifts > 0:
        for x in range(num_gifts):
            reward = Reward(rewarded_player=character.player,
                            rewarded_character=character,
                            is_improvement=False,
                            is_ported_reward=True)
            reward.save()
    elif num_gifts < 0:
        num_to_void = num_gifts * -1
        gifts_to_void = character.reward_set \
            .filter(is_void=False, is_improvement=False, is_ported_reward=True) \
            .all()[:num_to_void]
        for gift in gifts_to_void:
            gift.mark_void()
    if num_improvements > 0:
        for x in range(num_improvements):
            reward = Reward(rewarded_player=character.player,
                            rewarded_character=character,
                            is_improvement=True,
                            is_ported_reward=True)
            reward.save()
    elif num_improvements < 0:
        num_to_void = num_improvements * -1
        improvements_to_void = character.reward_set \
                            .filter(is_void=False, is_improvement=True, is_ported_reward=True) \
                            .all()[:num_to_void]
        for improvement in improvements_to_void:
            improvement.mark_void()
