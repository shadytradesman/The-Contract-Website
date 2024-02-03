from django import template

register = template.Library()

@register.simple_tag
def player_can_edit_power(power, player):
    return power.parent_power.player_can_edit(player)

@register.inclusion_tag('powers/power_badge_snippet.html')
def discovery_power_badge(power_full):
    latest_revision = power_full.latest_revision()
    character = power_full.character if power_full.character else None
    return {
        'discovery_page': True,
        'power_full': power_full,
        'latest_revision': latest_revision,
        'character': character,
        'show_status_warning': False,
    }

@register.inclusion_tag('powers/power_badge_snippet.html', takes_context=True)
def power_rev_badge(context, power, force_show_warnings=False, crafter_blurb=None, artifact=None, can_edit=False):
    request = context["request"] if "request" in context else None
    power_full = power.parent_power
    character = power_full.character if power_full.character else None
    show_status_warning = force_show_warnings
    if character:
        show_status_warning = not power.passes_status_check(character.status)
    show_active_toggle = can_edit and power.show_status_toggle(artifact)
    is_active = show_active_toggle
    if show_active_toggle:
        is_active = power.get_is_active(artifact)
    art_id = artifact.id if artifact else None
    if character or force_show_warnings:
        reward_count = power_full.reward_count()
        at_least_one_gift = power_full.reward_count(include_improvements=False)
    else:
        reward_count = 0
        at_least_one_gift = True
    return {
        'discovery_page': False,
        'force_show_warnings': force_show_warnings,
        'power_full': power_full,
        'latest_revision': power,
        'character': character,
        'show_status_warning': show_status_warning,
        'crafter_blurb': crafter_blurb,
        'show_active_toggle': show_active_toggle,
        'is_active': is_active,
        'art_id': art_id,
        'reward_count': reward_count,
        'at_least_one_gift': at_least_one_gift,
        'can_edit': can_edit,
        'is_early_access': request.user.is_authenticated and request.user.profile.early_access_user
    }

@register.inclusion_tag('powers/power_badge_snippet.html', takes_context=True)
def power_badge(context, power_full, force_show_warnings=False, artifact=None, can_edit=False, rewarding_character=None, is_stock=False):
    request = context["request"] if "request" in context else None
    latest_revision = power_full.latest_revision()
    character = rewarding_character if rewarding_character else power_full.character if power_full.character else None
    force_show_warnings = force_show_warnings and not is_stock
    show_status_warning = force_show_warnings
    if character and (not is_stock or rewarding_character):
        if character.is_stock:
            show_status_warning = False
        else:
            show_status_warning = not latest_revision.passes_status_check(character.status)
    show_active_toggle = can_edit and latest_revision.show_status_toggle(artifact)
    is_active = show_active_toggle
    if show_active_toggle:
        is_active = latest_revision.get_is_active(artifact)
    art_id = artifact.id if artifact else None
    gift_cost = power_full.get_gift_cost()
    if not is_stock and (character or force_show_warnings):
        if character and character.is_stock:
            reward_count = power_full.get_gift_cost()
            at_least_one_gift = True
        else:
            reward_count = power_full.reward_count()
            at_least_one_gift = power_full.reward_count(include_improvements=False)
    else:
        reward_count = 0
        at_least_one_gift = True
    return {
        'discovery_page': False,
        'force_show_warnings': force_show_warnings,
        'power_full': power_full,
        'latest_revision': latest_revision,
        'character': character,
        'rewarding_character': rewarding_character,
        'show_status_warning': show_status_warning,
        'show_active_toggle': show_active_toggle,
        'is_active': is_active,
        'art_id': art_id,
        'is_stock': is_stock,
        'reward_count': reward_count,
        'at_least_one_gift': at_least_one_gift,
        'gift_cost': gift_cost,
        'can_edit': can_edit,
        'is_early_access': request.user.is_authenticated and request.user.profile.early_access_user
    }

@register.inclusion_tag('powers/ps2_view_pages/heading_snip.html')
def power_heading(power, power_full=None):
    latest_revision = power
    power_full = power.parent_power if power_full is None else power_full
    character = power_full.character if power_full.character_id else None
    show_status_warning = False
    if character:
        show_status_warning = not latest_revision.passes_status_check(character.status)
    return {
        'discovery_page': False,
        'power_full': power_full,
        'latest_revision': latest_revision,
        'show_status_warning': show_status_warning,
    }
