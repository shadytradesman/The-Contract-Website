from django.templatetags.static import static
from django.template.loader import render_to_string
from collections import defaultdict

import re

from characters.models import Ability, Limit, StockBattleScar, MINOR_SCAR, MAJOR_SCAR, SEVERE_SCAR, EXTREME_SCAR,\
    StockWorldElement, CONDITION, CIRCUMSTANCE, TROPHY, TRAUMA

# Support for "STML" or Spencer Text Markup Language
# This is a super-janky markup language that is intended only for admin use.
# DO NOT GIVE USERS ACCESS TO THESE METHODS. THEY ARE NOT SECURE OR EVEN REALLY STABLE.
def render_content(unrendered_content, pics_by_slug):
    rendered_content = __render_section_links(str(unrendered_content))
    rendered_content = __render_columns(rendered_content)
    rendered_content = __render_gm_tip(rendered_content)
    rendered_content = __render_examples(rendered_content)
    rendered_content = __render_images(rendered_content, pics_by_slug)
    rendered_content = __render_fancy_sections(rendered_content)
    return rendered_content

def __render_images(content, pics_by_slug):
    return re.sub(r"(<p>[\s]*)?\{![\s]*image(-sm)? ([\w./-]+)[\s]+([\w\./\s\'\,\"\(\)\?\-\!]*)!\}([\s]*</p>)?",
                  lambda x: '<span class="css-guide-image{}"><img src=\'{}\'></span><span class="css-guide-image-caption">{}</span>'.format(
                      x.group(2) if x.group(2) else "",
                      pics_by_slug[x.group(3)].picture.url,
                      x.group(4),
                  ),
                  content)


# {{article-slug|link-text}} to link to that article
def __render_section_links(content):
    return re.sub(r"\{\{([\w-]+)\|([\w\s-]+)\}\}", r"<a href=#\1>\2</a>", content)


# {!col1!} {!col2!} {!colend!}
def __render_columns(content):
    col1_start = '<div class="row"><div class="col-md-6 col-xs-12">'
    col2_start = '</div><div class="col-md-6 col-xs-12">'
    col_end = '</div></div>'
    rendered_content = re.sub(r"(<p>[\s]*)?\{!col1!\}([\s]*</p>)?", col1_start, content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!col2!\}([\s]*</p>)?", col2_start, rendered_content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!colend!\}([\s]*</p>)?", col_end, rendered_content)
    return rendered_content


def __render_gm_tip(content):
    start = '<div class="css-gm-tip"><div class="css-gm-tip-header"><div class="css-guide-image-xs" style="background-image: url(\'{}\')"></div> GM Tip</div><div class="css-gm-tip-content">' \
        .format(static("guide/graphics/Sky_D10.png"))
    end = '</div></div>'
    rendered_content = re.sub(r"(<p>[\s]*)?\{!start-gm-tip!\}([\s]*</p>)?", start, content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!end-gm-tip!\}([\s]*</p>)?", end, rendered_content)
    return rendered_content


def __render_examples(content):
    start = '<div class="css-examples">' \
            '<a class="wiki-entry-collapsible" role="button">' \
            '<div class="css-examples-header"><div class="css-guide-image-xs" style="background-image: url(\'{}\')">' \
            '</div> {} <small style="font-size: 12px; font-weight: 400;">(<span class="visible-xs-inline visible-sm-inline">tap</span><span class="hidden-xs hidden-sm">click</span> to expand)</small></div>' \
            '</a>' \
            '<div class="css-examples-content collapse-content"  style="display:none;">' \
        .format(static("guide/graphics/Pink_D10.png"), r"\2")
    end = '</div></div>'
    rendered_content = re.sub(r"(<p>[\s]*)?\{!start-examples\|([\w\s]+)!\}([\s]*</p>)?", start, content)
    rendered_content = re.sub(r"(<p>[\s]*)?\{!end-examples!\}([\s]*</p>)?", end, rendered_content)
    return rendered_content


def __fancy_abilities():
    abilities = Ability.objects.filter(is_primary=True).order_by("name").all()
    return render_to_string("guide/rendered-sections/abilities.html", {"abilities": abilities})

def __fancy_primary_limits():
    limits = Limit.objects.filter(is_default=True, is_primary=True).order_by("name").all()
    return render_to_string("guide/rendered-sections/limits.html", {"limits": limits})

def __fancy_alt_limits():
    limits = Limit.objects.filter(is_default=False, is_primary=True).order_by("name").all()
    return render_to_string("guide/rendered-sections/limits.html", {"limits": limits})

def __fancy_battle_scars():
    minor_scars = StockBattleScar.objects.filter(type=MINOR_SCAR).order_by("description").all()
    major_scars = StockBattleScar.objects.filter(type=MAJOR_SCAR).order_by("description").all()
    severe_scars = StockBattleScar.objects.filter(type=SEVERE_SCAR).order_by("description").all()
    extreme_scars = StockBattleScar.objects.filter(type=EXTREME_SCAR).order_by("description").all()
    return render_to_string("guide/rendered-sections/scars.html", {
        "scar_categories": [minor_scars, major_scars, severe_scars, extreme_scars]
    })


def __fancy_world_element(element_type):
    stock_elements = StockWorldElement.objects.filter(type=element_type).exclude(category__name="creation-only").order_by("category").all()
    options = []
    current_options = []
    current_category = stock_elements[0].category
    for element in stock_elements:
        if element.category != current_category:
            options.append((current_category.name, current_options))
            current_options = []
            current_category = element.category
        current_options.append((element.name, element.description, element.system))
    options.append((current_category.name, current_options))
    return render_to_string("guide/rendered-sections/world_elements.html", {"elements": options})


def __fancy_conditions():
    return __fancy_world_element(CONDITION)

def __fancy_circumstances():
    return __fancy_world_element(CIRCUMSTANCE)


def __fancy_traumas():
    return __fancy_world_element(TRAUMA)


def __fancy_trophies():
    return __fancy_world_element(TROPHY)


content_methods = {
    "abilities": __fancy_abilities,
    "primary_limits": __fancy_primary_limits,
    "alternative_limits": __fancy_alt_limits,
    "battle_scars": __fancy_battle_scars,
    "conditions": __fancy_conditions,
    "circumstances": __fancy_circumstances,
    "traumas": __fancy_traumas,
    "trophies": __fancy_trophies,
}

def __render_fancy_sections(content):
    return re.sub(r"(<p>[\s]*)?\{\{([\w-]+)\}\}([\s]*</p>)?", lambda x: content_methods[x.group(2)](), content)


# Render text on save. Replaces
# {{fancy-section}} with entire section
