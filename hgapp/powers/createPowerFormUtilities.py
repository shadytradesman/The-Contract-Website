from django.utils import timezone
from .models import Power, DICE_SYSTEM,  MIND_, BODY_, PARRY_

from characters.models import Roll, Attribute, Ability, NO_PARRY_INFO, REACTION, THROWN


def _get_roll_initial_ability(roll):
    if roll.ability:
        return roll.ability.id
    else:
        return None


def _get_roll_initial_attribute(roll):
    if roll.attribute:
        return roll.attribute.id
    elif roll.is_mind:
        return MIND_
    elif roll.is_body:
        return BODY_
    elif roll.parry_type != NO_PARRY_INFO:
        return PARRY_
    else:
        raise ValueError("Unknown roll attribute")


def refund_or_assign_rewards(new_power, old_power=None):
    og_point_value = 0
    if old_power:
        og_point_value = old_power.parent_power.reward_count()
    delta = new_power.get_gift_cost() - og_point_value
    print(delta)
    if delta == 0:
        return
    if delta > 0:
        if new_power.parent_power.character is not None:
            unspent_gifts = new_power.parent_power.character.unspent_rewards()
            for a in range(delta):
                if a == len(unspent_gifts):
                    break
                unspent_gifts[a].assign_to_power(new_power)
    if delta < 0:
        if new_power.parent_power.character is not None and old_power:
            spent_gifts = old_power.parent_power.reward_list()
            for a in range(delta*-1):
                if a == len(spent_gifts):
                    break
                spent_gifts[a].refund_keeping_character_assignment()


def _get_power_from_form(power_form, base):
    return Power(name=power_form.cleaned_data['power_name'],
                  flavor_text=power_form.cleaned_data['flavor'],
                  description=power_form.cleaned_data['description'],
                  system=power_form.cleaned_data['system'],
                  base=base,
                  dice_system=DICE_SYSTEM[1][0],
                  pub_date=timezone.now())
