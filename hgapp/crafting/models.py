from django.db import models

from characters.models import Artifact, Character
from games.models import Game_Attendance
from powers.models import Power, Power_Full

# Crafting Constants
NUM_FREE_CONSUMABLES_PER_DOWNTIME = 1
NUM_FREE_CONSUMABLES_PER_REWARD = 2
NUM_FREE_ARTIFACTS_PER_DOWNTIME = 0
NUM_FREE_ARTIFACTS_PER_REWARD = 1


class CraftingEvent(models.Model):
    # many to many because one power_full can create multiple artifacts or consumable stacks
    artifacts = models.ManyToManyField(Artifact,
                                       through="CraftedArtifact",
                                       through_fields=('relevant_crafting', 'relevant_artifact'))
    # nullable because contractors may craft before their first Contract with Gifted or charon coin
    relevant_attendance = models.ForeignKey(Game_Attendance, on_delete=models.CASCADE, blank=True, null=True)
    # if pre-imbue (no attendance), this field is necessary to determine contractor who did the crafting.
    relevant_character = models.ForeignKey(Character, on_delete=models.CASCADE) # for pre-imbue

    relevant_power = models.ForeignKey(Power, on_delete=models.CASCADE) # Needed when calculating exp costs, etc.

    relevant_power_full = models.ForeignKey(Power_Full, on_delete=models.CASCADE)

    # user-provided notes on the crafting? Is this needed?
    detail = models.CharField(max_length=1500, null=True, blank=True)

    class Meta:
        unique_together = (
            ("relevant_attendance", "relevant_power_full"),
        )

        indexes = [
            models.Index(fields=['relevant_power_full']),
            models.Index(fields=['relevant_attendance']),
        ]


# Exists so we can figure out which artifacts were crafted in an event. Useful when changing attendances of characters.
# Also so Artifacts know when they were made.
class CraftedArtifact(models.Model):
    relevant_artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    relevant_crafting = models.ForeignKey(CraftingEvent, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    quantity_free = models.PositiveIntegerField(default=0)  # Free crafted items are voided when gifts are changed.
    is_refundable = models.BooleanField(default=True)
    exp_spent = models.IntegerField(default=0)  # For easy Exp calculations?

    class Meta:
        unique_together = (
            ("relevant_artifact", "relevant_crafting"),
        )

        indexes = [
            models.Index(fields=['quantity_free']),
            models.Index(fields=['is_refundable']),
        ]

