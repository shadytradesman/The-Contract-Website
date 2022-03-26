from django.contrib import admin

from .models import CraftingEvent, CraftedArtifact

admin.site.register(CraftedArtifact)
admin.site.register(CraftingEvent)
