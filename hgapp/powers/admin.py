from django.contrib import admin

from .forms import EnhancementDrawbackPickerForm, TagPickerForm
from django.utils.html import mark_safe
from django.db.models import Q

from django.urls import reverse

from .models import Enhancement, Parameter, Base_Power, Drawback, Power_Param, Power, Parameter_Value, \
    Base_Power_Category, Base_Power_System, PowerTag, PremadeCategory,\
    Enhancement_Instance, Drawback_Instance, Power_Full, PowerTutorial, SystemFieldText, SystemFieldRoll, \
    ParameterFieldSubstitution, BasePowerFieldSubstitution, EnhancementFieldSubstitution, DrawbackFieldSubstitution,\
    EFFECT, VECTOR, MODALITY, SYS_LEGACY_POWERS, SYS_ALL, SYS_PS2, FieldSubstitutionMarker


class PowerParamTabular(admin.StackedInline):
    model = Power_Param
    extra = 0


class SystemFieldTextTabular(admin.TabularInline):
    model = SystemFieldText
    extra = 0


class SystemFieldRollTabular(admin.TabularInline):
    model = SystemFieldRoll
    extra = 0


class ParameterFieldSubTabular(admin.TabularInline):
    model = ParameterFieldSubstitution
    extra = 0


class EnhancementFieldSubTabular(admin.TabularInline):
    model = EnhancementFieldSubstitution
    extra = 0


class DrawbackFieldSubTabular(admin.TabularInline):
    model = DrawbackFieldSubstitution
    extra = 0


class BasePowerFieldSubTabular(admin.TabularInline):
    model = BasePowerFieldSubstitution
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


@admin.register(Enhancement)
class EnhancementAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [EnhancementFieldSubTabular]
    filter_horizontal = ["required_Enhancements", "required_drawbacks"]
    list_per_page = 2000

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "required_Enhancements":
            kwargs["queryset"] = Enhancement.objects.order_by("is_general", "name")
        if db_field.name == "required_drawbacks":
            kwargs["queryset"] = Drawback.objects.order_by("is_general", "name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Drawback)
class DrawbackAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [DrawbackFieldSubTabular]
    filter_horizontal = ["required_Enhancements", "required_drawbacks"]
    list_per_page = 2000

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "required_Enhancements":
            kwargs["queryset"] = Enhancement.objects.order_by("is_general", "name")
        if db_field.name == "required_drawbacks":
            kwargs["queryset"] = Drawback.objects.order_by("is_general", "name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ParameterFieldSubTabular]


@admin.register(Base_Power)
class BasePowerAdmin(admin.ModelAdmin):
    list_per_page = 2000
    ordering = ("-base_type", "name")
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'base_type', 'category', 'is_public')
    inlines = [PowerParamTabular, SystemInline, BasePowerFieldSubTabular]
    filter_horizontal = ["enhancements", "drawbacks", "substitutions", "avail_enhancements", "avail_drawbacks",
                         "blacklist_parameters", "blacklist_enhancements", "blacklist_drawbacks",
                         "allowed_vectors", "allowed_modalities"]
    fieldsets = (
        (None, {
            'fields': (('name', 'slug'),
                       ('summary', 'is_public'),
                       ('base_type', 'num_free_enhancements'),
                       ('required_status', 'category'),
                       ('description', 'eratta'),
                       'avail_enhancements', 'avail_drawbacks')
        }),
        ('Show component restrictions', {
            'classes': ('collapse',),
            'fields': ('allowed_vectors', 'allowed_modalities'),
        }),
        ('Show legacy Enhancements and Drawbacks', {
            'classes': ('collapse',),
            'fields': ('enhancements', 'drawbacks'),
        }),
        ('Show blacklists', {
            'classes': ('collapse',),
            'fields': ('blacklist_parameters', 'blacklist_enhancements', 'blacklist_drawbacks'),
        }),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "allowed_vectors":
            kwargs["queryset"] = Base_Power.objects.filter(base_type=VECTOR)
        if db_field.name == "allowed_modalities":
            kwargs["queryset"] = Base_Power.objects.filter(base_type=MODALITY)
        if db_field.name == "enhancements":
            kwargs["queryset"] = Enhancement.objects\
                .filter(Q(system=SYS_ALL) | Q(system=SYS_LEGACY_POWERS))\
                .order_by("is_general", "name")
        if db_field.name == "drawbacks":
            kwargs["queryset"] = Drawback.objects\
                .filter(Q(system=SYS_ALL) | Q(system=SYS_LEGACY_POWERS))\
                .order_by("is_general", "name")
        if db_field.name in ["avail_enhancements", "blacklist_enhancements"]:
            kwargs["queryset"] = Enhancement.objects\
                .filter(Q(system=SYS_ALL) | Q(system=SYS_PS2))\
                .order_by("name")
        if db_field.name in ["avail_drawbacks", "blacklist_drawbacks"]:
            kwargs["queryset"] = Drawback.objects\
                .filter(Q(system=SYS_ALL) | Q(system=SYS_PS2))\
                .order_by("name")
        if db_field.name == "blacklist_parameters":
            kwargs["queryset"] = Parameter.objects.order_by("name")

        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Base_Power_System)
class BasePowerSystemAdmin(admin.ModelAdmin):
    inlines = [SystemFieldTextTabular, SystemFieldRollTabular]


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
    readonly_fields = ('pub_date', 'parent_power')


@admin.register(Power_Full)
class PowerFullAdmin(admin.ModelAdmin):
    list_display = ('name', 'base')
    readonly_fields = ('pub_date',)


admin.site.register(Power_Param)
admin.site.register(FieldSubstitutionMarker)
admin.site.register(Parameter_Value)
admin.site.register(Enhancement_Instance)
admin.site.register(Drawback_Instance)
admin.site.register(PowerTutorial)
admin.site.register(SystemFieldText)
admin.site.register(SystemFieldRoll)