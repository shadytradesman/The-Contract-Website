from django.contrib import admin
from .models import UserImage, PrivateUserImage

@admin.register(UserImage)
class UserImageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_date')

@admin.register(PrivateUserImage)
class PrivateUserImageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_date')
