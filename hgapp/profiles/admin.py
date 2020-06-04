from django.contrib import admin
from profiles.models import Profile
# Register your models here.

@admin.register(Profile)
class PowerAdmin(admin.ModelAdmin):
    pass