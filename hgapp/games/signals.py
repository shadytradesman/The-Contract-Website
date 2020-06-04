from django.db.models.signals import pre_delete
from django.dispatch import receiver
from games.models import Game_Attendance

# This is done as a signal instead of model override due to django doc recommendation
@receiver(pre_delete, sender=Game_Attendance, dispatch_uid="delete_attendance")
def set_default_character_view_permissions(sender, instance, **kwargs):
    if instance.attending_character:
        instance.attending_character.default_perms_char_and_powers_to_player(instance.relevant_game.creator)
