from django.contrib import admin

# Register your models here.
from characters.models import Character, Graveyard_Header, Character_Death

admin.site.register(Character)
admin.site.register(Character_Death)
admin.site.register(Graveyard_Header)