from django.contrib import admin

from .models import CraftingEvent, CraftedArtifact

@admin.register(CraftingEvent)
class AdminCraftingEvent(admin.ModelAdmin):
    fields = ('relevant_attendance', 'relevant_character', 'relevant_power', 'relevant_power_full', 'detail', 'total_exp_spent')
    readonly_fields = ('relevant_power', 'relevant_power_full')


admin.site.register(CraftedArtifact)
