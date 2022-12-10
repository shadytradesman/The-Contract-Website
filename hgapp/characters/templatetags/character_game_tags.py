from django import template
from django.template.loader import render_to_string
from characters.models import LOOSE_END

register = template.Library()

@register.inclusion_tag('characters/element_snip.html')
def render_element(scenario_element, grant_element_form, show_grant_form=True):
    return {
        "element": scenario_element.relevant_element,
        "is_loose_end": scenario_element.relevant_element.type == LOOSE_END,
        "scenario_element": scenario_element,
        "grant_element_form":  grant_element_form,
        "show_grant_form": show_grant_form,
    }


def render_scenario_element(scenario_element, request):
    return render_to_string(
        'characters/element_snip.html',
        render_element(scenario_element, None, False),
        request)
