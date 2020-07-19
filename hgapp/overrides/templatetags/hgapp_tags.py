from django import template

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