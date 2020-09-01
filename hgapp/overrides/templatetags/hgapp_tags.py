from django import template
from django.shortcuts import get_object_or_404
from wiki.models import Article, URLPath

register = template.Library()

@register.inclusion_tag('tags/gwynn_art.html')
def gwynn_jpg(filename):
    return {
        'filename': filename,
        'ext': ".jpg"
    }

@register.inclusion_tag('tags/gwynn_art.html')
def gwynn_png(filename):
    return {
        'filename': filename,
        'ext': ".png"
    }

@register.inclusion_tag('tags/article_toc.html')
def article_toc(article_path=None):
    article = None
    if not article_path:
        root = URLPath.root()
        article = root.article
    else:
        urlpath = URLPath.get_by_path(article_path, select_related=True)
        article = urlpath.article
    toc_tree = article.get_children(
        article__current_revision__deleted=False)
    return {
        'article_children': toc_tree,
        'article': article,
    }