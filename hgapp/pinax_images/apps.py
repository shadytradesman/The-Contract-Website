from django.apps import AppConfig

# This app exists to allow the blog app to migrate
class PinaxImagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pinax_images'
