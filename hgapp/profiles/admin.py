from django.contrib import admin
from profiles.models import Profile
# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'early_access_user', 'is_private', 'date_confirmed_agreements', 'num_player_games', 'num_games_gmed')