from django.contrib import admin

# Register your models here.
from characters.models import Character, Graveyard_Header, Character_Death, Attribute, Ability, Asset, Liability, \
    CharacterTutorial, ContractStats, Limit, LiabilityDetails, AssetDetails, AttributeValue, AbilityValue, ExperienceReward, \
    TraumaRevision, Condition, Circumstance, Artifact, Roll


class AbilityValueTabular(admin.TabularInline):
    model = AbilityValue
    extra = 0

class AttributeValueTabular(admin.TabularInline):
    model = AttributeValue
    extra = 0

class AssetDetailsTabular(admin.TabularInline):
    model = AssetDetails
    extra = 0

class LiabilitiesDetailsTabular(admin.TabularInline):
    model = LiabilityDetails
    extra = 0

class TraumaRevisionTabular(admin.TabularInline):
    model = TraumaRevision
    extra = 0

@admin.register(ContractStats)
class ContractStatsAdmin(admin.ModelAdmin):
    inlines = [AbilityValueTabular, AttributeValueTabular, AssetDetailsTabular, LiabilitiesDetailsTabular, TraumaRevisionTabular]

admin.site.register(Character)
admin.site.register(Character_Death)
admin.site.register(Graveyard_Header)
admin.site.register(Attribute)
admin.site.register(Ability)
admin.site.register(Asset)
admin.site.register(Liability)
admin.site.register(CharacterTutorial)
admin.site.register(Limit)
admin.site.register(ExperienceReward)
admin.site.register(Condition)
admin.site.register(Circumstance)
admin.site.register(Artifact)
admin.site.register(Roll)
