from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.urls import reverse
from guardian.shortcuts import assign_perm, remove_perm
import requests
import random
import hashlib

from hgapp.utilities import get_queryset_size, get_object_or_none

from games.games_constants import get_completed_game_excludes_query

from .permissionUtilities import default_manage_memberships, default_manage_roles, default_post_events, \
    default_manage_characters, default_manage_games, default_edit_world

ROLE = (
    ('LEADER', 'Leader'),
    ('JUDGE', 'Judge'),
    ('MEMBER', 'Member'),
    ('WATCHER', 'Watcher'),
)

# NEVER CHANGE THIS ORDERING.
CELL_PERMISSIONS = (
    ('admin', "Administrate"), # change roles, everything else.
    ('manage_memberships', 'Manage Memberships'), #ranks and recruitment
    ('manage_roles', 'Run Games'), # change to: can run games?
    ('post_events', 'Post World Events'),
    ('manage_member_characters', 'Manage Contractors'),
    ('edit_world', 'Edit Playgroup'),
    ('manage_games', 'Manage Games'),
)

def random_string():
    return hashlib.sha224(bytes(random.randint(1, 99999999))).hexdigest()

class Cell(models.Model):
    name = models.CharField(max_length=200)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='cell_creator',
        on_delete=models.PROTECT)
    created_date = models.DateTimeField('date created',
                                        auto_now_add=True)
    find_world_date = models.DateTimeField('find world date',
                                           null=True,
                                           blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     through="CellMembership",
                                     through_fields=('relevant_cell', 'member_player'))

    # Invites
    invitations = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         through="CellInvite",
                                         related_name='cell_invites')
    invite_link_secret_key = models.CharField(default=random_string,
                                              max_length=64)
    allow_self_invites = models.BooleanField(default=False)

    # Setting information
    setting_name = models.CharField(max_length=200) # prepopulate name field with this value for migration purposes
    setting_sheet_blurb = models.CharField(max_length=500, default=" ")
    setting_summary = models.CharField(max_length=10000, null=True, blank=True)
    setting_description = models.TextField(max_length=70000,
                                           null=True,
                                           blank=True)
    setting_create_char_info = models.CharField(max_length=10000, null=True, blank=True)

    # Cell Info
    cell_sell = models.CharField(max_length=10000, null=True, blank=True)
    house_rules = models.CharField(max_length=50000, null=True, blank=True)
    community_link = models.CharField(max_length=1000, null=True, blank=True)
    is_community_link_public = models.BooleanField(default=False)
    is_listed_publicly = models.BooleanField(default=False)
    are_contractors_portable = models.BooleanField(default=True)
    #TODO: how are games played? In person, on roll-20, on discord? online?

    game_victory = models.IntegerField(null=True, blank=True)
    game_loss = models.IntegerField(null=True, blank=True)
    game_death = models.IntegerField(null=True, blank=True)

    def get_danger_display(self):
        if not self.game_victory or not self.game_loss or not self.game_death:
            self.update_safety_stats()
        num_games = self.num_completed_games()
        game_death_ratio = self.death_ratio()
        if num_games < 3:
            return None
        elif game_death_ratio < 0.01 and num_games > 4:
            result = "Pillow"
        elif game_death_ratio < 0.05:
            result = "Safe"
        elif game_death_ratio < 0.13:
            result = "Average"
        elif game_death_ratio < 0.25:
            result = "Dangerous"
        elif game_death_ratio < 0.4:
            result = "Deadly"
        elif game_death_ratio < 1:
            result = "Hell"
        else:
            result = "Slaughterhouse"

        return "<span class=\"css-difficulty css-difficulty-{}\">{}</span>".format(result, result)

    def death_ratio(self):
        return self.game_death / (self.game_victory + self.game_loss + 1) # prevent divide-by-zero errors

    def update_safety_stats(self):
        completed_games = self.game_set.exclude(get_completed_game_excludes_query()).all()
        num_victory = 0
        num_died = 0
        num_loss = 0
        for game in completed_games:
            num_died = num_died + game.number_deaths()
            num_victory = num_victory + game.number_victories()
            num_loss = num_loss + game.number_losses()
        self.game_victory = num_victory
        self.game_loss = num_loss
        self.game_death = num_died
        self.save()

    def get_danger_tooltip(self):
        return "Victories: {} <br>Losses: {} <br>Deaths: {}".format(self.game_victory, self.game_loss, self.game_death)

    def player_can_admin(self, player):
        return player.has_perm(CELL_PERMISSIONS[0][0], self)

    def player_can_manage_memberships(self, player):
        return player.has_perm(CELL_PERMISSIONS[1][0], self)

    def player_can_run_games(self, player):
        return player.has_perm(CELL_PERMISSIONS[2][0], self)

    def player_can_post_world_events(self, player):
        return player.has_perm(CELL_PERMISSIONS[3][0], self)

    def player_can_edit_characters(self, player):
        return player.has_perm(CELL_PERMISSIONS[4][0], self)

    def player_can_edit_world(self, player):
        return player.has_perm(CELL_PERMISSIONS[5][0], self)

    def player_can_manage_games(self, player):
        return player.has_perm(CELL_PERMISSIONS[6][0], self)

    def get_player_membership(self, player):
        return get_object_or_none(self.cellmembership_set.filter(member_player=player))

    def get_permissions_for_role(self, role):
        return get_object_or_none(PermissionsSettings, relevant_cell=self, role=role)

    def __str__(self):
        return self.name

    def resetShareLink(self):
        self.invite_link_secret_key = random_string()
        self.save()

    def getGroupName(self, role):
        return "cell-" + str(self.pk) + role

    def addPlayer(self, player, role):
        if self.get_player_membership(player):
            raise ValueError("player already in cell")
        membership = CellMembership(
            relevant_cell=self,
            member_player=player,
            role = role[0],
        )
        membership.save()
        invite = get_object_or_none(self.cellinvite_set.filter(invited_player = player))
        if invite:
            invite.membership = membership
            invite.save()
        return membership

    def removePlayer(self, player):
        membership = get_object_or_none(self.cellmembership_set.filter(member_player = player))
        if not membership:
            raise ValueError("player not in cell")
        if self.player_is_only_leader(player):
            raise ValueError("Cannot remove only leader")
        membership = self.cellmembership_set.get(member_player=player)
        membership.remove_user_from_all_groups()
        membership.remove_characters_from_cell()
        membership.delete()

    def player_is_only_leader(self, player):
        membership = get_object_or_none(self.cellmembership_set.filter(member_player = player))
        if not membership:
            return False
        return membership.role == ROLE[0][0] and get_queryset_size(self.cellmembership_set.filter(role=ROLE[0][0])) == 1

    def invitePlayer(self, player, text):
        extant_invite = get_object_or_none(self.cellinvite_set.filter(invited_player = player))
        if extant_invite:
            if extant_invite.is_declined:
                extant_invite.is_declined = False
                extant_invite.save()
                return extant_invite
            else:
                raise ValueError("Cannot invite someone already invited")
        else:
            invite = CellInvite(
                relevant_cell = self,
                invited_player = player,
                invite_text = text,
            )
            invite.save()
            return invite

    def number_of_members(self):
        return self.cellmembership_set.count()

    def completed_games(self):
        return self.completed_games_queryset().all()

    def num_completed_games(self):
        return self.completed_games_queryset().count()

    def completed_games_queryset(self):
        return self.game_set \
            .exclude(get_completed_game_excludes_query())\
            .order_by("-end_time")

    def num_games_player_participated(self, player):
        completed_games = self.completed_games()
        return len([game for game in completed_games if game.player_participated(player)])

    def save(self, *args, **kwargs):
        if self.setting_sheet_blurb and self.setting_sheet_blurb[-1] == '.':
            self.setting_sheet_blurb = self.setting_sheet_blurb[:-1 or None]
        if not hasattr(self, "find_world_date") or not self.find_world_date:
            self.find_world_date = self.created_date
        if self.pk is None:
            super(Cell, self).save(*args, **kwargs)
            for role in ROLE:
                group = Group.objects.create(name = self.getGroupName(role[0]))
                if role == ROLE[0]:
                    #leader group gets all the perms. It is not configurable via settings.
                    for permission in CELL_PERMISSIONS:
                        assign_perm(permission[0], group, self)
                settings = PermissionsSettings(relevant_cell=self, role=role[0])
                settings.save()
            self.addPlayer(player=self.creator, role=ROLE[0])
        else:
            super(Cell, self).save(*args, **kwargs)

    def open_invitations(self):
        return self.cellinvite_set.filter(is_declined = False, membership = None).all()

    class Meta:
        permissions = CELL_PERMISSIONS

class WorldEvent(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='event_creator',
        on_delete=models.CASCADE)
    parent_cell = models.ForeignKey(
        Cell,
        related_name='happened_in_cell',
        on_delete=models.CASCADE)
    created_date = models.DateTimeField('date created',
                                        auto_now_add=True)
    headline = models.CharField(max_length=1000)
    event_description = models.TextField(max_length=50000,
                                      null=True,
                                      blank=True)

    def get_permalink(self, request):
        return "{}#event-{}".format(request.build_absolute_uri(reverse('cells:cells_view_cell', args=(self.parent_cell.id,))), self.id)


class WebHook(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='hook_creator',
        on_delete=models.CASCADE)
    parent_cell = models.ForeignKey(
        Cell,
        related_name='webhook_cell',
        on_delete=models.CASCADE)
    created_date = models.DateTimeField('date created',
                                        auto_now_add=True)
    url = models.CharField(max_length=2000,
                           help_text="The Discord webhook's URL")
    mention_group_id = models.BigIntegerField(blank=True,
                                           null=True,
                                           help_text="Optional. The Discord group ID to @mention when this webhook posts. Find by typing "
                                                     "'\\@GROUPNAME' in your Discord server and copying the number.")
    send_for_contracts = models.BooleanField(default=True)
    send_for_events = models.BooleanField(default=True)
    send_for_new_members = models.BooleanField(default=True)

    def __str__(self):
        return "{} {}{}{} hook".format(self.parent_cell.name, self.send_for_contracts, self.send_for_events, self.send_for_new_members)

    def post(self, content):
        if hasattr(self, "mention_group_id") and self.mention_group_id:
            content = "<@&{}> {}".format(str(self.mention_group_id), content)
        requests.post(self.url, json={'content': content})

    def post_new_membership(self, player, cell, request):
        content = "{} has joined {}! See their profile here: {}".format(
            player.username,
            cell.name,
            request.build_absolute_uri(reverse('profiles:profiles_view_profile', args=(player.id,))))
        return self.post(content)

    def post_for_event(self, event, request):
        content = "**{}**\nRead More: {}".format(
            event.headline,
            event.get_permalink(request))
        return self.post(content)


class CellMembership(models.Model):
    relevant_cell = models.ForeignKey(Cell,
                                      on_delete=models.CASCADE)
    member_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      on_delete=models.CASCADE)
    role = models.CharField(choices=ROLE,
                            max_length=20)
    joined_date = models.DateTimeField('date created',
                                        auto_now_add=True)

    def add_user_to_current_group(self):
        groupName = self.relevant_cell.getGroupName(self.role)
        group = Group.objects.get(name=groupName)
        self.member_player.groups.add(group)

    def remove_user_from_all_groups(self):
        for role in ROLE:
            groupName = self.relevant_cell.getGroupName(role[0])
            group = Group.objects.get(name=groupName)
            self.member_player.groups.remove(group)

    def remove_characters_from_cell(self):
        for character in self.member_player.character_set.filter(cell=self.relevant_cell, is_deleted=False):
            character.cell = None
            character.save()

    def __str__(self):
        return self.member_player.username

    # prevent double membership
    class Meta:
        unique_together = (("relevant_cell", "member_player"))

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(CellMembership, self).save(*args, **kwargs)
        else:
            if self.role != ROLE[0][0] and self.relevant_cell.player_is_only_leader(self.member_player):
                raise ValueError("Cannot remove only leader")
            self.remove_user_from_all_groups()
            super(CellMembership, self).save(*args, **kwargs)
        self.add_user_to_current_group()


class PermissionsSettings(models.Model):
    relevant_cell = models.ForeignKey(Cell,
                                      on_delete=models.CASCADE)
    role = models.CharField(choices=ROLE,
                            max_length=20)

    can_manage_memberships = models.BooleanField()
    can_manage_roles = models.BooleanField()
    can_post_events = models.BooleanField()
    can_manage_member_characters = models.BooleanField()
    can_edit_world = models.BooleanField()
    can_manage_games = models.BooleanField()

    def setting_for_perm(self, permission):
        if permission == CELL_PERMISSIONS[0]:
            raise ValueError("Admin permissions not configurable")
        if permission == CELL_PERMISSIONS[1]:
            return self.can_manage_memberships
        if permission == CELL_PERMISSIONS[2]:
            return self.can_manage_roles
        if permission == CELL_PERMISSIONS[3]:
            return self.can_post_events
        if permission == CELL_PERMISSIONS[4]:
            return self.can_manage_member_characters
        if permission == CELL_PERMISSIONS[5]:
            return self.can_edit_world
        if permission == CELL_PERMISSIONS[6]:
            return self.can_manage_games
        raise ValueError("Permission not found")

    def enabled_permissions(self):
        permissions = []
        if self.can_manage_memberships:
            permissions.append(CELL_PERMISSIONS[1])
        if self.can_manage_roles:
            permissions.append(CELL_PERMISSIONS[2])
        if self.can_post_events:
            permissions.append(CELL_PERMISSIONS[3])
        if self.can_manage_memberships:
            permissions.append(CELL_PERMISSIONS[4])
        if self.can_edit_world:
            permissions.append(CELL_PERMISSIONS[5])
        if self.can_manage_member_characters:
            permissions.append(CELL_PERMISSIONS[6])
        return permissions

    def updatePermissions(self):
        groupName = self.relevant_cell.getGroupName(self.role)
        group = Group.objects.get(name = groupName)
        for permission in CELL_PERMISSIONS[1:]:
            if self.setting_for_perm(permission):
                assign_perm(permission[0], group, self.relevant_cell)
            else:
                remove_perm(permission[0], group, self.relevant_cell)


    def save(self, *args, **kwargs):
        if self.pk is None:
            self.can_manage_memberships = default_manage_memberships(self.role)
            self.can_manage_roles = default_manage_roles(self.role)
            self.can_post_events = default_post_events(self.role)
            self.can_manage_member_characters = default_manage_characters(self.role)
            self.can_edit_world = default_edit_world(self.role)
            self.can_manage_games = default_manage_games(self.role)
        super(PermissionsSettings, self).save(*args, **kwargs)
        self.updatePermissions()

    # prevent double role settings
    class Meta:
        unique_together = (("relevant_cell", "role"))

class CellInvite(models.Model):
    invited_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.CASCADE)
    relevant_cell = models.ForeignKey(Cell,
                                      on_delete=models.CASCADE)
    invite_text = models.TextField(max_length=1000,
                                   null=True,
                                   blank=True)
    created_date = models.DateTimeField('date created',
                                        auto_now_add=True)
    is_declined = models.BooleanField(default=False)
    membership = models.OneToOneField(CellMembership,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)

    #prevent double invitations.
    class Meta:
        unique_together = (("invited_player", "relevant_cell"))

    def accept(self):
        self.is_declined = False
        self.save()
        self.relevant_cell.addPlayer(player=self.invited_player, role=ROLE[2])

    def reject(self):
        if self.membership:
            raise ValueError("can't reject invite for already accepted member")
        self.is_declined = True
        self.save()

    def save(self, *args, **kwargs):
        if self.pk is None:
            if self.relevant_cell.cellmembership_set.filter(member_player = self.invited_player):
                raise ValueError("User is already in cell")
            super(CellInvite, self).save(*args, **kwargs)
        else:
            super(CellInvite, self).save(*args, **kwargs)

