from django.db.models.signals import post_save
from django.dispatch import receiver
from characters.signals import transfer_consumables

from .models import CraftedArtifact

@receiver(transfer_consumables)
def handle_transfer_consumables(sender, **kwargs):
    original_artifact = kwargs["original_artifact"]
    new_artifact = kwargs["new_artifact"]
    quantity = kwargs["quantity"]
    power = kwargs["power"]
    crafted_artifacts = original_artifact.craftedartifact_set.order_by("-relevant_crafting__relevant_attendance__relevant_game__end_time").all()
    remaining_to_transfer = quantity
    for crafted_artifact in crafted_artifacts:
        if remaining_to_transfer == 0:
            break
        if remaining_to_transfer < 0:
            raise ValueError("transferring too many crafted artifacts")
        existing_crafted_artifact = new_artifact.craftedartifact_set.filter(relevant_crafting=crafted_artifact.relevant_crafting).first()
        if existing_crafted_artifact is None:
            existing_crafted_artifact = CraftedArtifact.objects.create(
                relevant_artifact=new_artifact,
                relevant_crafting=crafted_artifact.relevant_crafting,
                quantity=0,
            )
        num_to_move = min(crafted_artifact.quantity, remaining_to_transfer)
        free_to_move = min(num_to_move, crafted_artifact.quantity_free)
        crafted_artifact.quantity -= num_to_move
        crafted_artifact.quantity_free -= free_to_move
        crafted_artifact.save()
        existing_crafted_artifact.quantity += num_to_move
        existing_crafted_artifact.quantity_free += free_to_move
        existing_crafted_artifact.save()
        remaining_to_transfer -= quantity
    if remaining_to_transfer != 0:
        raise ValueError("Tried to transfer more consumables than were crafted?")
    power.artifacts.add(new_artifact)
    power.save()
    power.parent_power.artifacts.add(new_artifact)
    power.parent_power.save()
