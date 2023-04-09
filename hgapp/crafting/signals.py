from django.db.models.signals import post_save
from django.dispatch import receiver
from characters.signals import transfer_consumables
from powers.signals import gift_revision, gift_major_revision, gift_adjustment

from crafting.models import CraftedArtifact


@receiver(gift_adjustment)
def handle_gift_adjustment(sender, **kwargs):
    # update things that have been crafted this downtime. No improvements
    power_full = kwargs["power_full"]
    old_power = kwargs["old_power"]
    new_power = kwargs["new_power"]
    current_attendance = power_full.character.get_current_downtime_attendance()
    current_crafting_event = power_full.craftingevent_set.filter(relevant_attendance=current_attendance).first()
    if current_crafting_event:
        crafted_artifact_ids = current_crafting_event.artifacts.values_list("pk", flat=True)
        affected_artifacts = old_power.artifacts.filter(pk__in=crafted_artifact_ids).values_list("pk", flat=True)
        old_power.artifacts.remove(*affected_artifacts)
        new_power.artifacts.add(*affected_artifacts)
        current_crafting_event.relevant_power = new_power
        current_crafting_event.save()


@receiver(gift_revision)
def handle_gift_revision(sender, **kwargs):
    power_full = kwargs["power_full"]
    old_power = kwargs["old_power"]
    new_power = kwargs["new_power"]
    current_attendance = power_full.character.get_current_downtime_attendance()
    current_crafting_event = power_full.craftingevent_set.filter(relevant_attendance=current_attendance).first()
    if current_crafting_event:
        current_crafting_event.refund_all()
        current_crafting_event.relevant_power = new_power
        current_crafting_event.save()


@receiver(gift_major_revision)
def handle_gift_major_revision(sender, **kwargs):
    power_full = kwargs["power_full"]
    new_power = kwargs["new_power"]
    if power_full.character:
        current_attendance = power_full.character.get_current_downtime_attendance()
        current_crafting_event = power_full.craftingevent_set.filter(relevant_attendance=current_attendance).first()
    else:
        current_crafting_event = power_full.craftingevent_set.order_by("relevant_attendance__relevant_game__end_time").first()
    if current_crafting_event:
        current_crafting_event.refund_all()
        current_crafting_event.relevant_power = new_power
        current_crafting_event.save()
    for artifact in power_full.artifacts.all():
        artifact.since_revised = True
        artifact.save()


@receiver(transfer_consumables, weak=False, dispatch_uid="abc123")
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
