from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from guardian.shortcuts import assign_perm, remove_perm
import random
import hashlib

from hgapp.utilities import get_queryset_size, get_object_or_none

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
    ('admin', "Administrate"),
    ('manage_memberships', 'Manage Memberships'),
    ('manage_roles', 'Manage Role Permissions'),
    ('post_events', 'Post World Events'),
    ('manage_member_characters', 'Manage Member Characters'),
    ('edit_world', 'Edit The World Description'),
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
    members = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     through="CellMembership",
                                     through_fields=('relevant_cell', 'member_player'))
    invitations = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         through="CellInvite",
                                         related_name='cell_invites')
    invite_link_secret_key = models.CharField(default = random_string,
                                              max_length=64)


    #TODO: add dice system support.
    # Setting information
    setting_name =  models.CharField(max_length=200)
    setting_description = models.TextField(max_length=40000,
                                      null=True,
                                      blank=True)

    def player_can_edit_characters(self, player):
        return player.has_perm(CELL_PERMISSIONS[4][0], self)

    def player_can_admin(self, player):
        return player.has_perm(CELL_PERMISSIONS[0][0], self)

    def player_can_edit_world(self, player):
        return player.has_perm(CELL_PERMISSIONS[5][0], self)

    def player_can_manage_memberships(self, player):
        return player.has_perm(CELL_PERMISSIONS[1][0], self)

    def player_can_manage_games(self, player):
        return player.has_perm(CELL_PERMISSIONS[6][0], self)

    def get_player_membership(self, player):
        return get_object_or_none(self.cellmembership_set.filter(member_player=player))

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

    def save(self, *args, **kwargs):
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
    headline =  models.CharField(max_length=200)
    event_description = models.TextField(max_length=40000,
                                      null=True,
                                      blank=True)

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
        group = Group.objects.get(name = groupName)
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

