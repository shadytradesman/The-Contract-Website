from django.contrib import admin

from .models import FrontPageInfo, QuickStartInfo, ExampleAction


admin.site.register(FrontPageInfo)
admin.site.register(QuickStartInfo)
admin.site.register(ExampleAction)
