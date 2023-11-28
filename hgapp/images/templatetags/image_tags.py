from django import template

register = template.Library()

@register.inclusion_tag('images/image_thumb.html')
def image_thumb(image):
    return {
        'image': image,
    }
