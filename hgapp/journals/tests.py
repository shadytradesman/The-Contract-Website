from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.utils import IntegrityError

from characters.models import Character
from cells.models import Cell
from games.models import Game, Scenario, WIN, Game_Attendance, Game_Invite
from games.games_constants import GAME_STATUS
from profiles.signals import make_profile_for_new_user

from .models import Journal

class JournalModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')
        make_profile_for_new_user(None, self.user1)
        self.user2 = User.objects.create_user(
            username='jacob2', email='jacob@2…', password='top_secret')
        make_profile_for_new_user(None, self.user2)
        self.cell_owner = User.objects.create_user(
            username='jacob23', email='jacob@23…', password='top_secret')
        self.cell = Cell.objects.create(
            name = "cell name",
            creator = self.cell_owner,
            setting_name = "world name",
            setting_description = "Test description")
        self.char1 = Character.objects.create(
            name="testchar1",
            tagline="they test so bad!",
            player=self.user1,
            appearance="they're ugly because that's better.",
            age="13 years",
            sex="taco bell",
            concept_summary="generic but relatable",
            ambition="eat a dragon's heart",
            private=True,
            pub_date=timezone.now(),
            edit_date=timezone.now(),
            cell=self.cell)
        self.char2 = Character.objects.create(
            name="testchar2",
            tagline="they test so bad!",
            player=self.user1,
            appearance="they're ugly because that's better.",
            age="13 years",
            sex="taco bell",
            concept_summary="generic but relatable",
            ambition="eat a dragon's heart",
            private=True,
            pub_date=timezone.now(),
            edit_date=timezone.now(),
            cell=self.cell)
        self.game1 = Game(
            title="title",
            creator=self.user2,
            gm=self.user2,
            created_date=timezone.now(),
            scheduled_start_time=timezone.now(),
            actual_start_time=timezone.now(),
            end_time=timezone.now(),
            status=GAME_STATUS[6][0],
            cell=self.cell,
        )
        self.game1.save()
        self.attendance_game1_char1 = Game_Attendance(
            relevant_game=self.game1,
            notes="notes",
            outcome=WIN,
            attending_character=self.char1,
        )
        game_invite = Game_Invite(invited_player=self.user1,
                                  relevant_game=self.game1,
                                  as_ringer=False)
        self.attendance_game1_char1.save()
        game_invite.attendance = self.attendance_game1_char1
        game_invite.save()
        self.game1.give_rewards()
        self.game2 = Game(
            title="title",
            creator=self.user2,
            gm=self.user2,
            created_date=timezone.now(),
            scheduled_start_time=timezone.now(),
            actual_start_time=timezone.now(),
            end_time=timezone.now(),
            status=GAME_STATUS[6][0],
            cell=self.cell,
        )
        self.game2.save()
        self.attendance_game2_char1 = Game_Attendance(
            relevant_game=self.game2,
            notes="notes",
            outcome=WIN,
            attending_character=self.char1,
        )
        game_invite = Game_Invite(invited_player=self.user1,
                                  relevant_game=self.game2,
                                  as_ringer=False)
        self.attendance_game2_char1.save()
        game_invite.attendance = self.attendance_game2_char1
        game_invite.save()
        self.game1.give_rewards()

    def __make_journal(self,
                       title="title",
                       content="content",
                       writer=None,
                       game_attendance=None,
                       edit_date=timezone.now(),
                       is_downtime=False,
                       is_valid=False,
                       is_deleted=False,
                       contains_spoilers=True):
        journal = Journal(title=title,
                          content=content,
                          writer=writer,
                          game_attendance=game_attendance,
                          edit_date=edit_date,
                          is_downtime=is_downtime,
                          is_valid=is_valid,
                          is_deleted=is_deleted,
                          contains_spoilers=contains_spoilers)
        journal.save()
        return journal



    def test_no_two_same_game_journals(self):
        journal1 = self.__make_journal(writer=self.user1,
                                       game_attendance=self.attendance_game1_char1,
                                       is_downtime=False)
        journal2 = self.__make_journal(writer=self.user1,
                                   game_attendance=self.attendance_game1_char1,
                                   is_downtime=True)
        journal3 = self.__make_journal(writer=self.user1,
                                   game_attendance=self.attendance_game1_char1,
                                   is_downtime=True)
        journal4 = self.__make_journal(writer=self.user1,
                                       game_attendance=self.attendance_game2_char1,
                                       is_downtime=True)
        journal4 = self.__make_journal(writer=self.user1,
                                       game_attendance=self.attendance_game2_char1,
                                       is_downtime=True)
        journal5 = self.__make_journal(writer=self.user1,
                                       game_attendance=self.attendance_game2_char1,
                                       is_downtime=False,
                                       is_deleted=True)
        # This is allowed because one journal is deleted.
        journal5 = self.__make_journal(writer=self.user1,
                                       game_attendance=self.attendance_game2_char1,
                                       is_downtime=False,
                                       is_deleted=False)
        # cannot have two non-downtime journals for same game.
        with self.assertRaises(IntegrityError):
            self.__make_journal(writer=self.user1,
                                           game_attendance=self.attendance_game1_char1,
                                           is_downtime=False)
