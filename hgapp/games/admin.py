from django.contrib import admin

from games.models import Game, Game_Attendance, Scenario_Discovery, Reward, ScenarioTag, GameMedium, Game_Invite, Move, \
    ScenarioWriteup, Scenario, ScenarioApproval


@admin.register(ScenarioTag)
class ScenarioTagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("tag",)}

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("__str__", "creator", "is_wiki_editable", "is_valid", "num_words", "times_run")


@admin.register(ScenarioWriteup)
class ScenarioWriteupAdmin(admin.ModelAdmin):
    list_display = ("__str__", "scenario_writer", "created_date", "num_words", "is_deleted", "is_community_edit")


admin.site.register(Game)
admin.site.register(Game_Attendance)
admin.site.register(Game_Invite)
admin.site.register(Scenario_Discovery)
admin.site.register(Reward)
admin.site.register(GameMedium)
admin.site.register(Move)
admin.site.register(ScenarioApproval)
