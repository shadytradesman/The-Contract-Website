from django.contrib import admin

# Register your models here.
from characters.models import Character, Graveyard_Header, Character_Death, Attribute, Ability, Asset, Liability

admin.site.register(Character)
admin.site.register(Character_Death)
admin.site.register(Graveyard_Header)
admin.site.register(Attribute)
admin.site.register(Ability)
admin.site.register(Asset)
admin.site.register(Liability)