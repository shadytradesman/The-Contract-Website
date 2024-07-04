from django.apps import AppConfig


class CharactersConfig(AppConfig):
    name = 'characters'

    def ready(self):
        import characters.signals
        import characters.signal_receivers


