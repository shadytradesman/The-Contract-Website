from django.conf import settings
from django.db import models

# Create your models here.
from characters.models import Character, HIGH_ROLLER_STATUS
from guardian.shortcuts import assign_perm, remove_perm
from django.utils.html import mark_safe, escape, linebreaks

ACTIVATION_STYLE = (
    ('PASSIVE', 'Passive'),
    ('ACTIVE', 'Active'),
)

CREATION_REASON = (
    ('NEW', 'New'),
    ('IMPROVEMENT', 'Improvement'),
    ('REVISION', 'Revision'),
    ('ADJUSTMENT', 'Adjustment'),
)

DICE_SYSTEM = (
    ('ALL', 'All'),
    ('HOUSEGAMES15', 'House Games 1.5'),
)

class Enhancement(models.Model):
    name = models.CharField(max_length = 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length = 50,
                            primary_key = True)
    required_Enhancements = models.ManyToManyField("Enhancement",
                                                   blank = True)
    required_drawbacks = models.ManyToManyField("Drawback",
                                                blank=True)
    required_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=HIGH_ROLLER_STATUS[0])
    system = models.CharField(choices=DICE_SYSTEM,
                              max_length=25,
                              default=DICE_SYSTEM[0])
    description = models.CharField(max_length= 250)
    eratta = models.TextField(blank=True,
                              null=True)
    multiplicity_allowed = models.BooleanField(default=False)
    detail_field_label = models.CharField(blank=True,
                                          null=True,
                                          max_length=35)
    is_general = models.BooleanField(default=False)

    def __str__(self):
        return self.name + " [" + self.slug + "] (" + self.description + ")"

    def form_name(self):
        return self.slug + "-e-is_selected"

    def form_detail_name(self):
        return self.slug+"-e-detail_text"

    def display(self):
        return self.name + " (" + self.description + ")"


class Drawback(models.Model):
    name = models.CharField(max_length= 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key = True)
    required_Enhancements = models.ManyToManyField("Enhancement",
                                                   blank = True)
    required_drawbacks = models.ManyToManyField("Drawback",
                                                blank=True)
    required_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=HIGH_ROLLER_STATUS[0])
    system = models.CharField(choices=DICE_SYSTEM,
                              max_length=25,
                              default=DICE_SYSTEM[0])
    description = models.CharField(max_length = 250)
    eratta = models.TextField(blank=True,
                              null=True)
    multiplicity_allowed = models.BooleanField(default=False)
    detail_field_label = models.CharField(blank=True,
                                          null=True,
                                          max_length=35)
    is_general = models.BooleanField(default=False)

    def __str__(self):
        return self.name + " [" + self.slug + "] (" + self.description + ")"

    def form_name(self):
        return self.slug + "-d-is_selected"

    def form_detail_name(self):
        return self.slug+"-d-detail_text"

    def display(self):
        return self.name + " (" + self.description + ")"

class Parameter(models.Model):
    name = models.CharField(max_length= 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key = True)
    level_zero = models.CharField(max_length= 60)
    level_one = models.CharField(max_length= 60,
                                 blank=True,
                                 null=True)
    level_two = models.CharField(max_length= 60,
                                blank=True,
                                null=True)
    level_three = models.CharField(max_length= 60,
                                   blank=True,
                                   null=True)
    level_four = models.CharField(max_length= 60,
                                  blank=True,
                                  null=True)
    level_five = models.CharField(max_length= 60,
                                  blank=True,
                                  null=True)
    level_six = models.CharField(max_length= 60,
                                 blank=True,
                                 null=True)
    eratta = models.TextField(blank=True,
                              null=True)
    def display(self):
        return " ".join([self.name])

    def __str__(self):
        return " ".join([self.name]) + " [" +self.slug + "]"

    def get_levels(self):
        levels = []
        if hasattr(self, "level_zero") and self.level_zero:
            levels.append(self.level_zero)
        if hasattr(self, "level_one") and self.level_one:
            levels.append(self.level_one)
        if hasattr(self, "level_two") and self.level_two:
            levels.append(self.level_two)
        if hasattr(self, "level_three") and self.level_three:
            levels.append(self.level_three)
        if hasattr(self, "level_four") and self.level_four:
            levels.append(self.level_four)
        if hasattr(self, "level_five") and self.level_five:
            levels.append(self.level_five)
        if hasattr(self, "level_six") and self.level_six:
            levels.append(self.level_six)
        return levels


    def get_value_for_level(self, level):
        if level is 0:
            return self.level_zero
        if level is 1:
            return self.level_one
        if level is 2:
            return self.level_two
        if level is 3:
            return self.level_three
        if level is 4:
            return self.level_four
        if level is 5:
            return self.level_five
        if level is 6:
            return self.level_six
        raise ValueError

    def get_max_level(self):
        for n in range(7):
            if self.get_value_for_level(n) is None:
                return n
        return 7

class Base_Power_Category(models.Model):
    name = models.CharField(max_length = 25)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length = 25,
                            primary_key= True)
    description = models.CharField(max_length = 50)

    def __str__(self):
        return " ".join([self.name])


class Base_Power(models.Model):
    name = models.CharField(max_length= 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key = True)
    category = models.ForeignKey(Base_Power_Category,
                                 on_delete=models.PROTECT)
    summary = models.CharField(max_length=50)
    description = models.TextField(max_length=5000)
    eratta = models.TextField(blank = True,
                              null = True)
    default_activation_style = models.CharField(choices=ACTIVATION_STYLE,
                                                max_length=25,
                                                default=ACTIVATION_STYLE[0])
    parameters = models.ManyToManyField(Parameter,
                                        through="Power_Param",
                                        through_fields=('relevant_base_power', 'relevant_parameter'))
    enhancements = models.ManyToManyField(Enhancement)
    drawbacks = models.ManyToManyField(Drawback)
    required_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=HIGH_ROLLER_STATUS[0])
    is_public = models.BooleanField(default=True)
    num_free_enhancements = models.IntegerField(default=0)

    def __str__(self):
        return self.name + " (" + self.summary + ")"

    def example_powers(self):
        return Power_Full.objects.filter(base=self, tags__in=["example"])

class Base_Power_System(models.Model):
    base_power = models.ForeignKey(Base_Power,
                                   on_delete=models.PROTECT)
    dice_system = models.CharField(choices=DICE_SYSTEM,
                                   max_length=25,
                                   default=DICE_SYSTEM[1])
    system_text = models.TextField()
    eratta = models.TextField(blank=True,
                              null=True)
    class Meta:
        unique_together = (("base_power", "dice_system"))

    def __str__(self):
        return ":".join([self.base_power.name,str(self.dice_system)])

class Power_Param(models.Model):
    relevant_parameter = models.ForeignKey(Parameter,
                                           on_delete=models.CASCADE)
    relevant_base_power = models.ForeignKey(Base_Power,
                                            on_delete=models.CASCADE)
    seasoned = models.IntegerField("Seasoned Threshold")
    veteran = models.IntegerField("Veteran Threshold")
    default = models.IntegerField("Default Level")

    class Meta:
        unique_together = ("relevant_parameter", "relevant_base_power")

    def get_status_tag(self, level):
        switcher = {
            self.default : " (Default)",
            self.seasoned : " (Seasoned)",
            self.veteran : " (Veteran)",
        }
        if level in switcher:
            return switcher[level]
        else:
            return ""

    def __str__(self):
        return ":".join([str(self.relevant_parameter), self.relevant_base_power.name])

class Power_Full(models.Model):
    name = models.CharField(max_length = 500)
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=25)
    base = models.ForeignKey(Base_Power,
                             on_delete=models.PROTECT)
    private = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    linked_powers = models.ManyToManyField("Power_Full",
                                           blank=True, 
                                           through="Power_Link",
                                           through_fields=('parent_power', 'child_power'))
    pub_date = models.DateTimeField('date published')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True)
    character = models.ForeignKey(Character,
                                  blank=True,
                                  null=True,
                                  on_delete=models.CASCADE)
    tags = models.ManyToManyField("PowerTag",
                                   blank=True)
    example_description = models.CharField(max_length = 9000,
                                           blank=True,
                                           null=True)

    class Meta:
        permissions = (
            ('view_private_power_full', 'View private power full'),
            ('edit_power_full', 'Edit power full'),
        )

    def delete(self):
        self.character = None
        for reward in self.reward_list():
            reward.refund_keeping_character_assignment()
        self.is_deleted=True
        self.save()

    def save(self, *args, **kwargs):
        super(Power_Full, self).save(*args, **kwargs)
        if self.character:
            self.character.grant_initial_source_if_required()

    def player_manages_via_cell(self, player):
        if self.is_deleted:
            return False
        if self.character:
            if self.character.cell:
                if self.character.cell.player_can_edit_characters(player):
                    return True
        return False

    def player_can_edit(self, player):
        if self.is_deleted:
            return False
        is_owner = player == self.owner
        return is_owner or \
               self.player_manages_via_cell(player) or \
               (player.has_perm("edit_power_full", self) and self.player_can_view(player))

    def player_can_view(self, player):
        if self.is_deleted:
            return False
        is_owner = player == self.owner
        return is_owner or \
               not self.private or \
               player.has_perm("view_private_power_full", self) or \
               self.player_manages_via_cell(player)

    def latest_revision(self):
        return self.power_set.order_by('-pub_date').all()[0]

    def get_point_value(self):
        return self.power_set.order_by('-pub_date').all()[0].get_point_value()

    def set_self_and_children_privacy(self, is_private):
        if is_private:
            self.set_self_and_children_private()
        else:
            self.set_self_and_children_public()

    def set_self_and_children_private(self):
        self.private = True
        self.save()
        for power in self.power_set.all():
            power.private = True
            power.save()

    def reveal_history_to_player(self, player):
        assign_perm('view_power_full', player, self)
        assign_perm('view_private_power_full', player, self)
        for power in self.power_set.all():
            power.reveal_to_player(player)

    def lock_edits(self):
        remove_perm('powers.edit_power_full', self.owner)

    def default_perms_history_to_player(self, player):
        assign_perm('view_power_full', player, self)
        assign_perm('edit_power_full', player, self)
        if player != self.owner:
            remove_perm('view_private_power_full', player, self)
        for power in self.power_set.all():
            power.default_perms_to_player(player)

    def set_self_and_children_public(self):
        self.private = False
        self.save()
        for power in self.power_set.all():
            power.private = False
            power.save()

    def latest_archive_txt(self):
        return self.latest_revision().archive_txt()

    def reward_list(self):
        rewards = []
        for power in self.power_set.order_by("-pub_date").all():
            for reward in power.relevant_power.filter(is_void = False).order_by("-awarded_on").all():
                rewards.append(reward)
        return rewards

    def at_least_one_gift_assigned(self):
        for reward in self.reward_list():
            if not reward.is_improvement:
                return True
        return False

    def __str__(self):
        if self.owner:
            return self.name + " [" + self.owner.username + "]"
        else:
            return self.name + " [NO ASSOCIATED USER]"

class PowerTag(models.Model):
    tag = models.CharField(max_length=40)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=40,
                            primary_key=True)
    def __str__(self):
        return self.tag

class PremadeCategory(models.Model):
    name = models.CharField(max_length=500)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key=True)
    description = models.CharField(max_length=5000)
    is_generic = models.BooleanField(default=True)
    tags = models.ManyToManyField("PowerTag",
                                   blank=True)

class Power(models.Model):
    name = models.CharField(max_length = 100)
    flavor_text = models.TextField(max_length = 2000)
    description = models.TextField(max_length = 2000)
    parent_power = models.ForeignKey(Power_Full,
                                     blank=True,
                                     null=True,
                                     on_delete=models.CASCADE)
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=25)
    base = models.ForeignKey(Base_Power, on_delete=models.CASCADE)
    private = models.BooleanField(default=False)
    linked_powers = models.ManyToManyField("Power", blank=True)
    activation_style = models.CharField(choices=ACTIVATION_STYLE, max_length = 25)
    creation_reason = models.CharField(choices=CREATION_REASON, max_length = 25)
    creation_reason_expanded_text = models.TextField(max_length = 1500,
                                                     blank=True,
                                                     null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                                   blank=True,
                                   null=True)
    system = models.TextField(max_length = 2000)
    selected_enhancements = models.ManyToManyField(Enhancement,
                                                   blank=True,
                                                   through="Enhancement_Instance",
                                                   through_fields=('relevant_power', 'relevant_enhancement'))
    selected_drawbacks = models.ManyToManyField(Drawback,
                                                   blank=True,
                                                   through="Drawback_Instance",
                                                   through_fields=('relevant_power', 'relevant_drawback'))
    pub_date = models.DateTimeField('date published')
    parameter_values = models.ManyToManyField(Power_Param,
                                              through="Parameter_Value",
                                              through_fields=('relevant_power', 'relevant_power_param'))

    class Meta:
        permissions = (
            ('view_private_power', 'View private power'),
        )

    def player_manages_via_cell(self, player):
        if self.parent_power:
            if self.parent_power.character:
                if self.parent_power.character.cell:
                    if self.parent_power.character.cell.player_can_edit_characters(player):
                        return True
        return False

    def player_can_edit(self, player):
        is_owner = player == self.created_by
        return is_owner or \
               self.player_manages_via_cell(player) or \
               (player.has_perm("edit_power", self) and self.player_can_view(player))

    def player_can_view(self, player):
        is_owner = player == self.created_by
        return is_owner or not self.private or player.has_perm("view_private_power", self) or self.player_manages_via_cell(player)

    def get_point_value(self):
        cost_of_power = 1
        total_parameter_cost = 0
        for param_val in self.parameter_value_set.all():
            total_parameter_cost = total_parameter_cost + (param_val.value - param_val.relevant_power_param.default)
        return  cost_of_power \
                + self.selected_enhancements.count() \
                - self.base.num_free_enhancements \
                - self.selected_drawbacks.count() \
                + total_parameter_cost

    def reveal_to_player(self, player):
        assign_perm('view_power', player, self)
        assign_perm('view_private_power', player, self)

    def default_perms_to_player(self, player):
        assign_perm('view_power', player, self)
        if player != self.created_by:
            remove_perm('view_private_power', player, self)

    def render_system(self):
        default_system = linebreaks(escape(self.system))
        value_by_name = {param_val.relevant_power_param.relevant_parameter.name :
                             param_val.relevant_power_param.relevant_parameter.get_value_for_level(level=param_val.value)
                         for param_val in self.parameter_value_set.all()}
        rendered_system = default_system
        for name, value in value_by_name.items():
            replaceable_name = str.format("[[{}]]",
                                          name.lower().replace(" ", "-"))
            formatted_value = str.format("<b>{}</b>", value)

            rendered_system = rendered_system.replace(replaceable_name, formatted_value)
        return mark_safe(rendered_system)

    def archive_txt(self):
        output = "{}\nA {} point {} {} power\nCreated by {}\n"
        output = output.format(self.name, self.get_point_value(), self.get_activation_style_display(), self.base.name, self.created_by.username)
        output = output + "{}\nDescription: {}\nSystem: {}\n"
        output = output.format(self.flavor_text,self.description, self.system)
        output = output + "Parameters:\n-------------\n"
        for parameter_value in self.parameter_value_set.all():
            output = output + "{}"
            output = output.format(parameter_value.archive_txt())
        output = output + "Enhancements:\n-------------\n"
        for enhancement_instance in self.enhancement_instance_set.all():
            output = output + "{}"
            output = output.format(enhancement_instance.archive_txt())
        output = output + "Drawbacks:\n----------\n"
        for drawback_instance in self.drawback_instance_set.all():
            output = output + "{}"
            output = output.format(drawback_instance.archive_txt())
        return output

    def creation_reason_action_text(self):
        if self.creation_reason == CREATION_REASON[0][0]:
            return "new"
        if self.creation_reason == CREATION_REASON[1][0]:
            return "improving"
        if self.creation_reason == CREATION_REASON[2][0]:
            return "revising"
        if self.creation_reason == CREATION_REASON[3][0]:
            return "adjusting"

    def __str__(self):
        return self.name + " (" + self.description + ")"

class Power_Link(models.Model):
    parent_power = models.ForeignKey(Power_Full,
                                     related_name='parent_power',
                                     on_delete=models.CASCADE)
    child_power = models.ForeignKey(Power_Full,
                                    related_name='child_power',
                                    on_delete=models.CASCADE)

class Enhancement_Instance(models.Model):
    relevant_enhancement = models.ForeignKey(Enhancement,
                                             on_delete=models.PROTECT)
    relevant_power = models.ForeignKey(Power,
                                       on_delete=models.CASCADE)
    detail = models.CharField(max_length = 150,
                              null=True,
                              blank=True)

    def archive_txt(self):
        output = "{} ({}) "
        output = output.format(self.relevant_enhancement.name, self.relevant_enhancement.description)
        if self.detail:
            output = output + "{}: {}"
            output = output.format(self.relevant_enhancement.detail_field_label, self.detail)
        output = output + "\n"
        return output

    def __str__(self):
        if self.relevant_enhancement.detail_field_label:
            return "{} :: {} {}: {}".format(self.relevant_power.name,str(self.relevant_enhancement), self.relevant_enhancement.detail_field_label, self.detail)
        else:
            return "{} :: {}".format(self.relevant_power.name,str(self.relevant_enhancement))



class Drawback_Instance(models.Model):
    relevant_drawback = models.ForeignKey(Drawback, on_delete=models.CASCADE)
    relevant_power = models.ForeignKey(Power,
                                       on_delete=models.CASCADE)
    detail = models.CharField(max_length=150,
                              null=True,
                              blank=True)

    def archive_txt(self):
        output = "{} ({}) "
        output = output.format(self.relevant_drawback.name, self.relevant_drawback.description)
        if self.detail:
            output = output + "{}: {}"
            output = output.format(self.relevant_drawback.detail_field_label, self.detail)
        output = output + "\n"
        return output

    def __str__(self):
        if self.relevant_drawback.detail_field_label:
            return "{} :: {} {}: {}".format(self.relevant_power.name,str(self.relevant_drawback), self.relevant_drawback.detail_field_label, self.detail)
        else:
            return "{} :: {}".format(self.relevant_power.name,str(self.relevant_drawback))

class Parameter_Value(models.Model):
    relevant_power_param = models.ForeignKey(Power_Param, on_delete=models.CASCADE)
    relevant_power = models.ForeignKey(Power,
                                       on_delete=models.CASCADE)
    value = models.IntegerField()

    def __str__(self):
        return " ".join([str(self.relevant_power_param), str(self.relevant_power), str(self.value)])

    def get_level_description(self):
        return self.relevant_power_param.relevant_parameter.get_value_for_level(level=self.value)

    def archive_txt(self):
        output = "{}: level {} ({})\n"
        output = output.format(self.relevant_power_param.relevant_parameter.name, self.value, self.relevant_power_param.relevant_parameter.get_value_for_level(self.value))
        return output

    level_description = property(get_level_description)

class PowerTutorial(models.Model):
    modal_base = models.TextField(max_length=3000)
    modal_base_header = models.TextField(max_length=3000)
    modal_edit_header = models.TextField(max_length=3000)
    modal_edit = models.TextField(max_length=3000)
