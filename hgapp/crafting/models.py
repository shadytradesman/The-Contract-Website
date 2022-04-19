from collections import Counter

from django.db import models
from django.db.models import Q, Sum

from characters.models import Artifact, Character
from games.models import Game_Attendance
from powers.models import Power, Power_Full, CRAFTING_CONSUMABLE

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

    def get_exp_cost_per_consumable(self):
        return 2

    def get_exp_cost_per_artifact(self):
        return self.relevant_power.get_gift_cost()

    def refund_all(self):
        if self.relevant_power_full.crafting_type == CRAFTING_CONSUMABLE:
            num_to_refund = self.craftedartifact_set.aggregate(Sum('quantity'))['quantity__sum']
            self.refund_crafted_consumables(number_to_refund=num_to_refund)
        self.artifacts.clear()

    def refund_crafted_consumables(self, number_to_refund):
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
            self.total_exp_spent -= num_refunded * self.get_exp_cost_per_consumable()
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

    def set_crafted_artifacts(self, artifacts, allowed_number_free):
        existing_artifacts = self.craftedartifact_set.filter(relevant_artifact__is_deleted=False).all()
        craftings_by_art_id = {x.relevant_artifact_id: x for x in existing_artifacts}
        new_art_ids = set([x.pk for x in artifacts])
        artifacts_to_refund = set([x.relevant_artifact_id for x in existing_artifacts if x.relevant_artifact_id not in new_art_ids])
        existing_artifacts_by_id = {x.relevant_artifact_id : x.relevant_artifact for x in existing_artifacts}
        current_num_free = 0
        for artifact in existing_artifacts:
            if artifact.quantity_free > 0:
                current_num_free += 1
        num_free_refunded = 0
        for art_id in artifacts_to_refund:
            crafting = craftings_by_art_id[art_id]
            artifact = existing_artifacts_by_id[art_id]
            self.relevant_power.artifacts.remove(artifact)
            self.relevant_power_full.artifacts.remove(artifact)
            if crafting.quantity_free == 0:
                self.total_exp_spent -= self.get_exp_cost_per_artifact()
            else:
                num_free_refunded += 1
            crafting.delete()
            artifact.refresh_from_db()
            if artifact.power_full_set.count() == 0:
                artifact.delete()
        num_avail_free = allowed_number_free - current_num_free + num_free_refunded
        for artifact in artifacts:
            if artifact.character != self.relevant_character:
                raise ValueError("cannot craft artifact held by someone else.")
            if artifact.crafting_character != self.relevant_character:
                raise ValueError("cannot craft artifact crafted by someone else.")
            if artifact.pk not in craftings_by_art_id:
                if artifact.power_full_set.filter(id=self.relevant_power_full_id).first() is not None:
                    raise ValueError("cannot craft the same power_full onto an artifact twice.")
                quant_free = 0
                if num_avail_free > 0:
                    quant_free = 1
                    num_avail_free -= 1
                CraftedArtifact.objects.create(
                    relevant_artifact=artifact,
                    relevant_crafting=self,
                    quantity=1,
                    quantity_free=quant_free,)
                power_full = self.relevant_power_full
                power_full.artifacts.add(artifact)
                power_full.latest_rev.artifacts.add(artifact)
                power_full.latest_rev.save()
                power_full.save()
                if quant_free == 0:
                    self.total_exp_spent += self.get_exp_cost_per_artifact()
            else:
                # adjust free craftings if necessary
                crafting = craftings_by_art_id[artifact.pk]
                if crafting.quantity_free == 0 and num_avail_free > 0:
                    crafting.quantity_free = 1
                    crafting.save()
                    self.total_exp_spent -= self.get_exp_cost_per_artifact()
                    num_avail_free -= 1
        self.save()

    def craft_new_consumables(self, number_newly_crafted, new_number_free, power_full):
        print("Crafting new consumables")
        print(self.relevant_power_full)
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
            # new artifactCrafting
            existing_artifacts = self.relevant_character.artifact_set.filter(is_consumable=True, is_deleted=False).all()
            new_artifact = None
            for art in existing_artifacts:
                power = art.power_set.first()
                if power == self.relevant_power:
                    new_artifact = art
                    break
            if new_artifact:
                new_artifact.quantity += number_newly_crafted
                new_artifact.save()
            else:
                new_artifact = Artifact.objects.create(
                    name=self.relevant_power.name,
                    description=self.relevant_power.description,
                    crafting_character=self.relevant_character,
                    character=self.relevant_character,
                    creating_player=self.relevant_character.player,
                    is_consumable=True,
                    quantity=number_newly_crafted,)
                power_full.artifacts.add(new_artifact)
                power_full.latest_rev.artifacts.add(new_artifact)
                power_full.latest_rev.save()
                power_full.save()
            CraftedArtifact.objects.create(
                relevant_artifact=new_artifact,
                relevant_crafting=self,
                quantity=paid_crafted + new_number_free,
                quantity_free=new_number_free, )
        self.total_exp_spent += (paid_crafted * self.get_exp_cost_per_consumable())
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
