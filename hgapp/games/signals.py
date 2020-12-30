from django.db.models.signals import pre_delete
from django.dispatch import receiver
from games.models import Game_Attendance, Reward
from characters.signals import GrantAssetGift, VoidAssetGifts

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