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

    def refund_crafted_consumables(self, number_to_refund, exp_cost_per):
        remaining_to_refund = number_to_refund
        crafted_artifacts = self.craftedartifact_set.prefetch_related("relevant_artifact").all()
        num_refunded_by_crafted_artifact_id = Counter()
        # First refund the non-free ones.
        for crafted_artifact in crafted_artifacts:
            if remaining_to_refund == 0:
                break
            num_refunded = min(crafted_artifact.quantity - crafted_artifact.quantity_free, remaining_to_refund)
            crafted_artifact.quantity -= num_refunded
            num_refunded_by_crafted_artifact_id[crafted_artifact.pk] += num_refunded
            remaining_to_refund -= num_refunded
            self.total_exp_spent -= num_refunded * exp_cost_per
        # now refund free ones
        for crafted_artifact in crafted_artifacts:
            if remaining_to_refund == 0:
                break
            num_refunded = min(crafted_artifact.quantity_free, remaining_to_refund)
            num_refunded_by_crafted_artifact_id[crafted_artifact.pk] += num_refunded
            crafted_artifact.quantity_free -= num_refunded
            crafted_artifact.quantity -= num_refunded
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

    def craft_new_consumables(self, number_newly_crafted, new_number_free, exp_cost_per, power_full):
        paid_crafted = number_newly_crafted - new_number_free
        crafted_artifacts = self.craftedartifact_set.filter(relevant_artifact__is_deleted=False).prefetch_related("relevant_artifact").all()
        crafter_held_crafted_artifact = None
        for crafted_artifact in crafted_artifacts:
            if crafted_artifact.relevant_artifact.character == self.relevant_character:
                crafter_held_crafted_artifact = crafted_artifact
                break
        if crafter_held_crafted_artifact:
            crafter_held_crafted_artifact.quantity_free += new_number_free
            crafter_held_crafted_artifact.quantity += paid_crafted + new_number_free
            crafter_held_crafted_artifact.save()

            crafter_held_crafted_artifact.relevant_artifact.quantity += number_newly_crafted
            crafter_held_crafted_artifact.relevant_artifact.save()
        else:
            new_artifact = Artifact.objects.create(
                name=self.relevant_power.name,
                description=self.relevant_power.description,
                crafting_character=self.relevant_character,
                character=self.relevant_character,
                creating_player=self.relevant_character.player,
                is_consumable=True,
                quantity=number_newly_crafted,)
            CraftedArtifact.objects.create(
                relevant_artifact=new_artifact,
                relevant_crafting=self,
                quantity=paid_crafted + new_number_free,
                quantity_free=new_number_free, )
            power_full.artifacts.add(new_artifact)
            power_full.latest_rev.artifacts.add(new_artifact)
            power_full.latest_rev.save()
            power_full.save()
        self.total_exp_spent += (paid_crafted * exp_cost_per)
        self.save()


# Exists so we can figure out which artifacts were crafted in an event. Useful when changing attendances of characters.
# Also so Artifacts know when they were made.
class CraftedArtifact(models.Model):
    relevant_artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    relevant_crafting = models.ForeignKey(CraftingEvent, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1) # actual number
    quantity_free = models.PositiveIntegerField(default=0)  # number of quantity that were free. this <= quantity
    is_refundable = models.BooleanField(default=True)

    class Meta:
        unique_together = (
            ("relevant_artifact", "relevant_crafting"),
        )

        indexes = [
            models.Index(fields=['quantity_free']),
            models.Index(fields=['is_refundable']),
        ]

    def save(self, *args, **kwargs):
        if self.quantity_free > self.quantity:
            raise ValueError("A consumable crafted cannot have more free than quantity")
        super().save(*args, **kwargs)
