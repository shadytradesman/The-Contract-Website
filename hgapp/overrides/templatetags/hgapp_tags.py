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

@register.inclusion_tag('tags/article_toc.html')
def article_toc(article_slug=None):
    article = None
    if not article_slug:
        root = URLPath.root()
        article = root.article
    else:
        urlpath = URLPath.get_by_path(article_slug, select_related=True)
        article = urlpath.article
    toc_tree = article.get_children(
        article__current_revision__deleted=False)
    return {
        'article_children': toc_tree,
        'article': article,
        'article_path': article_slug + "/",
    }