from django.apps import AppConfig


class PowersConfig(AppConfig):
    name = 'powers'

    def ready(self):
        import powers.signals
