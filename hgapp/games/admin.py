from django.contrib import admin

from games.models import Game, Game_Attendance, Scenario_Discovery, Reward, ScenarioTag, GameMedium, Game_Invite


@admin.register(ScenarioTag)
class ScenarioTagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("tag",)}

admin.site.register(Game)
admin.site.register(Game_Attendance)
admin.site.register(Game_Invite)
admin.site.register(Scenario_Discovery)
admin.site.register(Reward)
admin.site.register(GameMedium)
