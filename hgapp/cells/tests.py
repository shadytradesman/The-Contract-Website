from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from hgapp.utilities import get_queryset_size
from cells.models import Cell, CELL_PERMISSIONS, ROLE

from cells.permissionUtilities import default_manage_memberships, default_manage_roles, default_post_events, \
    default_manage_characters, default_manage_games, default_edit_world


class CellModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')
        self.user2 = User.objects.create_user(
            username='jacob2', email='jacob@2…', password='top_secret')
        self.user3 = User.objects.create_user(
            username='jacob3', email='jacob@3…', password='top_secret')
        self.user4 = User.objects.create_user(
            username='jacob4', email='jacob@4…', password='top_secret')
        self.user5 = User.objects.create_user(
            username='jacob5', email='jacob@5…', password='top_secret')
        self.cell = Cell.objects.create(
                            name = "cell name",
                            creator = self.user1,
                            setting_name = "world name",
                            setting_description = "Test description")

    def test_change_permissions_settings(self):
        self.cell.addPlayer(self.user2, role=ROLE[1])
        self.assertTrue(self.user2.has_perm(CELL_PERMISSIONS[2][0], self.cell) == default_manage_roles(ROLE[1][0]))
        self.assertTrue(self.user2.has_perm(CELL_PERMISSIONS[3][0], self.cell) == default_post_events(ROLE[1][0]))
        settings = self.cell.permissionssettings_set.get(role=ROLE[1][0])
        settings.can_manage_roles = not default_manage_roles(ROLE[1][0])
        settings.can_post_events = not default_post_events(ROLE[1][0])
        settings.save()
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[2][0], self.cell) == default_manage_roles(ROLE[1][0]))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[3][0], self.cell) == default_post_events(ROLE[1][0]))


    def test_change_current_user_role(self):
        self.cell.addPlayer(self.user2, role=ROLE[0])
        self.assertTrue(self.user2.has_perm(CELL_PERMISSIONS[2][0], self.cell) == default_manage_roles(ROLE[0][0]))
        self.assertTrue(self.user2.has_perm(CELL_PERMISSIONS[3][0], self.cell) == default_post_events(ROLE[0][0]))
        membership = self.cell.cellmembership_set.get(member_player = self.user2)
        membership.role = ROLE[3][0]
        membership.save()
        self.assertTrue(self.user2.has_perm(CELL_PERMISSIONS[2][0], self.cell) == default_manage_roles(ROLE[3][0]))
        self.assertTrue(self.user2.has_perm(CELL_PERMISSIONS[3][0], self.cell) == default_post_events(ROLE[3][0]))

    def test_cell_creator_has_all_perms(self):
        for perm in CELL_PERMISSIONS:
            self.assertTrue(self.user1.has_perm(perm[0], self.cell))

    def test_user_not_in_cell_has_no_perms(self):
        for perm in CELL_PERMISSIONS:
            self.assertFalse(self.user2.has_perm(perm[0], self.cell))

    def test_added_user_has_proper_perms(self):
        users_roles = ((self.user2, ROLE[2]), (self.user3, ROLE[3]), (self.user4, ROLE[1]))
        for user_role in users_roles:
            self.cell.addPlayer(player=user_role[0], role=user_role[1])
            self.assertTrue(user_role[0].has_perm(CELL_PERMISSIONS[1][0], self.cell) == default_manage_memberships(user_role[1][0]))
            self.assertTrue(user_role[0].has_perm(CELL_PERMISSIONS[2][0], self.cell) == default_manage_roles(user_role[1][0]))
            self.assertTrue(user_role[0].has_perm(CELL_PERMISSIONS[3][0], self.cell) == default_post_events(user_role[1][0]))
            self.assertTrue(user_role[0].has_perm(CELL_PERMISSIONS[4][0], self.cell) == default_manage_characters(user_role[1][0]))
            self.assertTrue(user_role[0].has_perm(CELL_PERMISSIONS[5][0], self.cell) == default_edit_world(user_role[1][0]))
            self.assertTrue(user_role[0].has_perm(CELL_PERMISSIONS[6][0], self.cell) == default_manage_games(user_role[1][0]))

    def test_banned_user_has_proper_perms(self):
        self.cell.addPlayer(self.user2, role=ROLE[0])
        self.cell.remove_player(self.user2)
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[1][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[2][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[3][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[4][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[5][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[6][0], self.cell))

        self.cell.addPlayer(self.user2, role=ROLE[0])
        for perm in CELL_PERMISSIONS:
            self.assertTrue(self.user2.has_perm(perm[0], self.cell))

        self.cell.ban_player(self.user2, "they sucked")
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[1][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[2][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[3][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[4][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[5][0], self.cell))
        self.assertFalse(self.user2.has_perm(CELL_PERMISSIONS[6][0], self.cell))

    def test_cant_remove_only_leader(self):
        with self.assertRaises(ValueError):
            self.cell.remove_player(self.user1)
        self.cell.addPlayer(self.user2, role=ROLE[0])
        self.cell.remove_player(self.user1)
        self.assertEqual(self.cell.cellmembership_set.get(role = ROLE[0][0]).member_player, self.user2, "User 2 should be only leader")
        with self.assertRaises(ValueError):
            self.cell.remove_player(self.user2)

    def test_cant_remove_non_member(self):
        with self.assertRaises(ValueError):
            self.cell.remove_player(self.user2)
        self.cell.addPlayer(self.user2, role=ROLE[0])
        self.cell.remove_player(self.user1)
        self.assertFalse(self.cell.cellmembership_set.filter(member_player = self.user1))
        self.assertTrue(self.cell.cellmembership_set.filter(member_player = self.user2))
 
    def test_cannot_add_player_twice(self):
        with self.assertRaises(ValueError):
            self.cell.addPlayer(self.user1, role=ROLE[2])

    def test_invite_player_and_accept(self):
        invite = self.cell.invitePlayer(self.user2, text="invite text")
        self.assertTrue(self.user2.cellinvite_set.get(relevant_cell = self.cell))
        self.assertEqual(get_queryset_size(self.cell.members), 1)
        self.assertFalse(self.cell.cellmembership_set.filter(member_player = self.user2))
        self.assertEqual(len(self.cell.open_invitations()), 1)
        invite.accept()
        self.assertEqual(get_queryset_size(self.cell.members), 2)
        self.assertTrue(self.cell.cellmembership_set.filter(member_player=self.user2))
        self.assertEqual(len(self.cell.open_invitations()), 0)

    def test_adding_player_closes_invites(self):
        self.cell.invitePlayer(self.user2, text="invite text")
        self.assertEqual(len(self.cell.open_invitations()), 1)
        self.cell.addPlayer(self.user2, role = ROLE[1])
        self.assertEqual(len(self.cell.open_invitations()), 0)


    def test_invite_player_rejected_not_in_active_invites(self):
        invite = self.cell.invitePlayer(self.user2, text="invite text")
        self.assertEqual(len(self.cell.open_invitations()), 1)
        invite.reject()
        self.assertEqual(len(self.cell.open_invitations()), 0)

    def test_invite_player_reject_not_member(self):
        invite = self.cell.invitePlayer(self.user2, text="invite text")
        invite.reject()
        self.assertFalse(self.cell.cellmembership_set.filter(member_player=self.user2))

    def test_reject_invite_after_member_fails(self):
        self.cell.invitePlayer(self.user2, text="invite text")
        self.cell.addPlayer(self.user2, role=ROLE[1])
        with self.assertRaises(ValueError):
            self.cell.cellinvite_set.get(invited_player=self.user2).reject()

    def test_can_invite_player_who_left(self):
        invite = self.cell.invitePlayer(self.user2, text="invite text")
        invite.accept()
        self.assertEqual(len(self.cell.open_invitations()), 0)
        self.cell.remove_player(player=self.user2)
        reinvite = self.cell.invitePlayer(self.user2, text="invite text")
        self.assertEqual(len(self.cell.open_invitations()), 1)
        reinvite.accept()
        self.assertEqual(len(self.cell.open_invitations()), 0)

        # Same thing but without accepting invites
        self.cell.invitePlayer(self.user3, text="invite text")
        self.cell.addPlayer(self.user3, role=ROLE[1])
        self.assertEqual(len(self.cell.open_invitations()), 0)
        self.cell.remove_player(player=self.user3)
        reinvite = self.cell.invitePlayer(self.user3, text="invite text")
        self.assertEqual(len(self.cell.open_invitations()), 1)
        reinvite.accept()
        self.assertEqual(len(self.cell.open_invitations()), 0)