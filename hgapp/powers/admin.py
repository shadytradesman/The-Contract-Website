from django.contrib import admin

from .forms import EnhancementDrawbackPickerForm, TagPickerForm
from django.utils.html import mark_safe

from django.urls import reverse

from .models import Enhancement, Parameter, Base_Power, Drawback, Power_Param, Power, Parameter_Value, \
    Base_Power_Category, Base_Power_System, PowerTag, PremadeCategory,\
    Enhancement_Instance, Drawback_Instance, Power_Full, PowerTutorial, SystemField

class PowerParamTabular(admin.TabularInline):
    model = Power_Param
    extra = 0

class SystemFieldTabular(admin.TabularInline):
    model = SystemField
    extra = 0

class SystemInline(admin.StackedInline):
    model = Base_Power_System
    fields = ['system_fields', 'base_power', 'dice_system', 'system_text', 'eratta',]
    readonly_fields = ('system_fields',)

    # description functions like a model field's verbose_name
    def system_fields(self, instance):
        if instance.id:
            changeform_url = reverse(
                'admin:powers_base_power_system_change', args=(instance.id,)
            )
            return mark_safe(u'<a href="%s" target="_blank">Edit System Fields</a>' % changeform_url)
        return u''
    extra = 0

class ParamValueTabular(admin.TabularInline):
    model = Parameter_Value
    extra = 0

class EnhancementInstanceTabular(admin.TabularInline):
    model = Enhancement_Instance
    extra = 0

class DrawbackInstanceTabular(admin.TabularInline):
    model = Drawback_Instance
    extra = 0

@admin.register(Enhancement)
class EnhancementAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Drawback)
class DrawbackAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Base_Power)
class BasePowerAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'category', 'is_public')
    inlines = [PowerParamTabular, SystemInline]
    filter_horizontal = ["enhancements", "drawbacks"]

@admin.register(Base_Power_System)
class BasePowerAdmin(admin.ModelAdmin):
    inlines = [SystemFieldTabular]

@admin.register(PowerTag)
class PowerTagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("tag",)}

@admin.register(PremadeCategory)
class PremadeCategoryAdmin(admin.ModelAdmin):
    form = TagPickerForm
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'is_generic')
    filter_horizontal = ["tags"]

@admin.register(Base_Power_Category)
class BasePowerCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Power)
class PowerAdmin(admin.ModelAdmin):
    inlines = [ParamValueTabular, EnhancementInstanceTabular, DrawbackInstanceTabular]
    list_display = ('name', 'base')

@admin.register(Power_Full)
class PowerAdmin(admin.ModelAdmin):
    list_display = ('name', 'base')

admin.site.register(Power_Param)
admin.site.register(Parameter_Value)
admin.site.register(Enhancement_Instance)
admin.site.register(Drawback_Instance)
admin.site.register(PowerTutorial)
admin.site.register(SystemField)
