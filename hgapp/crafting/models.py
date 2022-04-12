from collections import Counter

from django.db import models

from characters.models import Artifact, Character
from games.models import Game_Attendance
from powers.models import Power, Power_Full

# Crafting Constants
NUM_FREE_CONSUMABLES_PER_DOWNTIME = 1
NUM_FREE_CONSUMABLES_PER_REWARD = 1
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

    total_exp_spent = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (
            ("relevant_attendance", "relevant_power_full"),
        )

        indexes = [
            models.Index(fields=['relevant_power_full']),
            models.Index(fields=['relevant_attendance']),
            models.Index(fields=['relevant_character']),
        ]

    def change_quantity_crafted(self, number_newly_crafted, exp_cost_per):
        # number newly crafted can be negative, meaning that the consumables are to be refunded.
        if number_newly_crafted == 0:
            return
        if number_newly_crafted < 0:
            self.__refund_crafted_consumables(-number_newly_crafted, exp_cost_per)
        if number_newly_crafted > 0:
            self.__craft_new_consumables(number_newly_crafted, exp_cost_per)

    def refund_crafted_consumables(self, number_to_refund, exp_cost_per):
        remaining_to_refund = number_to_refund
        crafted_artifacts = self.craftedartifact_set.prefetch_related("relevant_artifact").all()
        num_refunded_by_crafted_artifact_id = Counter()
        # First refund the non-free ones.
        for crafted_artifact in crafted_artifacts:
            if remaining_to_refund == 0:
                break
            num_refunded = min(crafted_artifact.quantity, remaining_to_refund)
            crafted_artifact.quantity -= num_refunded
            num_refunded_by_crafted_artifact_id[crafted_artifact.pk] += num_refunded
            remaining_to_refund -= num_refunded
            crafted_artifact.exp_spent -= num_refunded * exp_cost_per
            self.total_exp_spent -= num_refunded * exp_cost_per
        # now refund free ones
        for crafted_artifact in crafted_artifacts:
            if remaining_to_refund == 0:
                break
            num_refunded = min(crafted_artifact.quantity_free, remaining_to_refund)
            num_refunded_by_crafted_artifact_id[crafted_artifact.pk] += num_refunded
            crafted_artifact.quantity_free -= num_refunded
            remaining_to_refund -= num_refunded
        # correctness checking
        if remaining_to_refund != 0:
            raise ValueError("Could not refund an appropriate amount of crafted artifacts.")
        if self.total_exp_spent < 0:
            raise ValueError("Negative exp expenditure on crafting refund")
        # adjust artifact quantities and save
        for crafted_artifact in crafted_artifacts:
            num_refunded = num_refunded_by_crafted_artifact_id[crafted_artifact.pk]
            if num_refunded > 0:
                curr_quantity = crafted_artifact.relevant_artifact.quantity
                # they may have used some
                crafted_artifact.relevant_artifact.quantity = max(0, curr_quantity - num_refunded)
                crafted_artifact.relevant_artifact.save()
            crafted_artifact.save()
        self.save()

    def craft_new_consumables(self, number_newly_crafted, number_free, exp_cost_per):
        crafted_artifacts = self.craftedartifact_set.prefetch_related("relevant_artifact").all()
        crafter_held_crafted_artifact = None
        for crafted_artifact in crafted_artifacts:
            if crafted_artifact.relevant_artifact.character == self.relevant_character:
                crafter_held_crafted_artifact = crafted_artifact
                break
        if crafter_held_crafted_artifact:
            crafter_held_crafted_artifact.quantity_free
            # add to existing
            pass
        else:
            pass
            # make one that we hold



# Exists so we can figure out which artifacts were crafted in an event. Useful when changing attendances of characters.
# Also so Artifacts know when they were made.
class CraftedArtifact(models.Model):
    relevant_artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    relevant_crafting = models.ForeignKey(CraftingEvent, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    quantity_free = models.PositiveIntegerField(default=0)  # Free crafted items are voided when gifts are changed.
    is_refundable = models.BooleanField(default=True)
    exp_spent = models.PositiveIntegerField(default=0)  # For easy Exp calculations?

    class Meta:
        unique_together = (
            ("relevant_artifact", "relevant_crafting"),
        )

        indexes = [
            models.Index(fields=['quantity_free']),
            models.Index(fields=['is_refundable']),
        ]

