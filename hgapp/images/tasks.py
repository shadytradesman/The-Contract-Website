from celery import shared_task
import os.path
from django.conf import settings
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

from .models import PrivateUserImage


@shared_task(name="generate_thumbnail")
def generate_thumbnail(private_image_pk):
    private_image = PrivateUserImage.objects.get(pk=private_image_pk)
    if private_image.is_too_small_for_thumb():
        return "Image dimensions do not demand thumbnail"
    private_image = PrivateUserImage.objects.get(pk=private_image_pk)
    image = Image.open(private_image.image)
    image.thumbnail(settings.THUMB_SIZE, Image.ANTIALIAS)

    thumb_name, thumb_extension = os.path.splitext(private_image.image.name)
    thumb_extension = thumb_extension.lower()

    thumb_filename = thumb_name + '_thumb' + thumb_extension

    if thumb_extension in ['.jpg', '.jpeg']:
        file_extension = 'JPEG'
    elif thumb_extension == '.gif':
        file_extension = 'GIF'
    elif thumb_extension == '.png':
        file_extension = 'PNG'
    else:
        raise ValueError("Unrecognized file format")

    with BytesIO() as temp_thumb:
        image.save(temp_thumb, file_extension)
        temp_thumb.seek(0)
        private_image.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()))
        private_image.thumbnail_height = private_image.thumbnail.height
        private_image.thumbnail_width = private_image.thumbnail.width
        private_image.save()

    return "Completed successfully"

