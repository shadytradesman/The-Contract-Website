import json
from collections import defaultdict
from django.core.cache import cache

from django import template
from django.urls import reverse
from account.models import EmailAddress

from guide.models import GuideBook, GuideSection

register = template.Library()

@register.inclusion_tag('tags/gwynn_art.html')
def gwynn_jpg(filename, hide_caption=None):
    return {
        'filename': filename,
        'ext': ".jpg",
        'hide_caption': hide_caption,
    }

@register.inclusion_tag('tags/gwynn_art.html')
def gwynn_png(filename, hide_caption=None):
    return {
        'filename': filename,
        'ext': ".png",
        'hide_caption': hide_caption,
    }


@register.inclusion_tag('tags/guidebook_search_blob.html')
def guidebook_search_blob():
    sentinel = object()
    cache_key = "guidebook-search-blob"
    cache_contents = cache.get(cache_key, sentinel)
    if cache_contents is sentinel:
        index_blob = _get_guide_index_blob()
        cache.set(cache_key, index_blob, timeout=600)
        cache_contents = index_blob
    return cache_contents


def _get_guide_index_blob():
    sections = GuideSection.objects.filter(is_deleted=False, is_hidden=False).all()
    section_by_tag = defaultdict(list)
    for section in sections:
        search_hit = {
            "url": section.to_url(),
            "title": section.title,
        }
        tags = section.tags if section.tags else []
        tags.extend(section.title.split())
        for tag in tags:
            section_by_tag[tag.lower()].append(search_hit)
    return {
        'blob': json.dumps(dict(section_by_tag)),
    }


@register.inclusion_tag('tags/email_verified.html')
def email_verified(user):
    email = EmailAddress.objects.get_primary(user)
    return {
        "verified": email and email.verified,
        "email": email
    }


@register.inclusion_tag('tags/character_nav_list.html')
def characters_nav_list(user):
    characters = user.character_set.filter(is_deleted=False).order_by("-edit_date")[:5]
    characters_sorted = sorted(characters, key=lambda x: x.name)
    return {
        "characters": characters_sorted
    }

@register.inclusion_tag('tags/guidebook_toc.html', takes_context=True)
def guide_toc(context, guidebook=None):
    guidebooks = GuideBook.objects.order_by('position').all()

    highlight_how_to_play = context["request"].user.game_set.count() == 0 if "request" in context and context["request"].user.is_authenticated else True

    can_edit = context["request"].user.is_superuser if "request" in context and context["request"].user else False
    sections_by_book = []
    for book in guidebooks:
        if guidebook and book == guidebook:
            continue
        sections_by_book.append((book, book.get_sections_in_order(is_admin=can_edit),))
    if guidebook:
        sections_by_book.append((guidebook, guidebook.get_sections_in_order(is_admin=can_edit),))
    nav_list = __get_nav_list(sections_by_book, active_book=guidebook, highlight_how_to_play=highlight_how_to_play)
    context["nav_list"] = nav_list
    return context


def __get_nav_list(sections_by_book, active_book=None, highlight_how_to_play=False):
    nav_list = '<ul class="nav nav-pills nav-stacked {}">'.format("" if not active_book else "")
    for guidebook, sections in sections_by_book:
        guidebook_active = guidebook == active_book if active_book else False
        url = guidebook.redirect_url if hasattr(guidebook, "redirect_url") and guidebook.redirect_url \
            else "#" if guidebook_active else reverse('guide:read_guidebook', args=(guidebook.slug,))
        guidebook_expanded = guidebook.expanded if not active_book else guidebook_active
        book_class = "css-how-to-play-link" if highlight_how_to_play and guidebook.redirect_url else "css-active-book" if guidebook_active else ""
        nav_list = nav_list + '<li class="{}"><a href="{}" class="css-guide-index-book">{}</a>' \
            .format(book_class, url, guidebook.title)
        if guidebook_expanded:
            nav_list = nav_list + __get_nav_list_for_sections(sections, guidebook_active, url)
        nav_list = nav_list + '</li>'  # end guidebook list item
    nav_list = nav_list + "</ul>"
    return nav_list


def __get_nav_list_for_sections(sections, is_viewing_guidebook, guidebook_url):
    nav_list = '<ol class="nav nav-pills nav-stacked">'
    prev_section = None
    depth = 1
    num_sections = sections.count()
    for i, section in enumerate(sections):
        entry = ""
        if prev_section and prev_section.header_level < section.header_level:
            for x in range(section.header_level - prev_section.header_level):
                entry = entry + '<ol class="nav nav-pills nav-stacked css-inner-nav-list">'
                depth = depth + 1
        if prev_section and prev_section.header_level > section.header_level:
            for x in range(prev_section.header_level - section.header_level):
                entry = entry + "</ol>"
                depth = depth - 1
        section_url = "#{}".format(section.slug) if is_viewing_guidebook else "{}#{}".format(guidebook_url, section.slug)
        entry = entry + '<li role="presentation" class="{}"><a href="{}">{}</a></li>'.format(
            'js-last-section' if i == num_sections - 1 else "js-first-section" if i == 0 else "",
            section_url,
            section.title)
        nav_list = nav_list + entry
        prev_section = section
    for x in range(depth):
        nav_list = nav_list + "</ol>"
    return nav_list

