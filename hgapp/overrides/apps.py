from django.apps import AppConfig


class OverridesConfig(AppConfig):
    name = 'overrides'

    def ready(self):
        import overrides.signals
