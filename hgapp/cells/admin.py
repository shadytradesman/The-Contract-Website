from django.contrib import admin

from .models import Cell, CellMembership, CellInvite, PermissionsSettings, WebHook

admin.site.register(Cell)
admin.site.register(CellMembership)
admin.site.register(CellInvite)
admin.site.register(PermissionsSettings)
admin.site.register(WebHook)
