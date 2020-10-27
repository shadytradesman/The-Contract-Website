from django import template
from django.shortcuts import get_object_or_404
from wiki.models import Article, URLPath

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

@register.inclusion_tag('tags/article_list.html', takes_context=True)
def article_list(context, urlpath, depth):
    context['parent'] = urlpath
    context['children'] = get_article_children(article=urlpath.article, article__current_revision__deleted=False)
    context['depth'] = depth
    return context


@register.inclusion_tag('tags/article_toc.html')
def article_toc(article_slug=None, dropdown=True, current_article=None):
    return inner_article_toc(article_slug, dropdown=dropdown, current_article=current_article)

def inner_article_toc(article_slug=None, dropdown=True, current_article=None):
    article = None
    if not article_slug:
        root = URLPath.root()
        article = root.article
    else:
        urlpath = URLPath.get_by_path(article_slug, select_related=True)
        article = urlpath.article
    toc_tree = get_article_children(article,
                                    article__current_revision__deleted=False)
    return {
        'article_children': toc_tree,
        'article_parent': article,
        'article_path': article_slug + "/",
        'is_dropdown': dropdown,
        'current_article': current_article,
    }

def get_article_children(article, max_num=None, user_can_read=None, **kwargs):
    """NB! This generator is expensive, so use it with care!!"""
    cnt = 0
    for obj in article.articleforobject_set.filter(is_mptt=True):
        if user_can_read:
            objects = obj.content_object.get_children().filter(
                **kwargs).can_read(user_can_read)
        else:
            objects = obj.content_object.get_children().filter(**kwargs)
        ordered_objects = sorted(objects,
                key=lambda x: x.get_absolute_url())
        for child in ordered_objects:
            cnt += 1
            if max_num and cnt > max_num:
                return
            yield child