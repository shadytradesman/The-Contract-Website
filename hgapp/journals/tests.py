from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.utils import IntegrityError

from characters.models import Character, EXP_NEW_CHAR, EXP_JOURNAL, EXP_REWARD_VALUES, EXP_WIN_IN_WORLD_V2
from cells.models import Cell
from games.models import Game, Scenario, WIN, Game_Attendance, Game_Invite
from games.games_constants import GAME_STATUS
from profiles.signals import make_profile_for_new_user

from journals.models import Journal

EXP_WIN = EXP_REWARD_VALUES[EXP_WIN_IN_WORLD_V2]
JOURNAL_EXP = EXP_REWARD_VALUES[EXP_JOURNAL]
LIST_100_WORDS = [str(x) for x in range(100)]
LIST_270_WORDS = [str(x) for x in range(270)]
INVALID_JOURNAL_CONTENT = " ".join(LIST_100_WORDS)
VALID_JOURNAL_CONTENT = " ".join(LIST_270_WORDS)

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
        self.scenario = Scenario.objects.create(
            title="test scenario",
            summary="summary",
            description="blah",
            creator=self.user1,
            max_players=1,
            min_players=2)
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
            scenario=self.scenario,
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
            scenario=self.scenario,
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
        self.game2.give_rewards()

        self.games = []
        self.char1_attendances = []
        for x in range(10):
            new_game = Game(
                scenario=self.scenario,
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
            self.games.append(new_game)
            new_game.save()
            new_attendance = Game_Attendance(
                relevant_game=self.games[x],
                notes="notes",
                outcome=WIN,
                attending_character=self.char1,
            )
            self.char1_attendances.append(new_attendance)
            new_attendance.save()
            game_invite = Game_Invite(invited_player=self.user1,
                                      relevant_game=new_game,
                                      as_ringer=False)
            game_invite.attendance = new_attendance
            game_invite.save()
            new_game.give_rewards()

    def __make_journal(self,
                       title="title",
                       content=None,
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

    def test_journal_content_must_be_set_with_helper(self):
        with self.assertRaises(ValueError):
            self.__make_journal(writer=self.user1,
                                game_attendance=self.attendance_game1_char1,
                                content="content",
                                is_downtime=False)

    def test_journals_grant_correct_rewards(self):
        for x in range(6):
            journal = self.__make_journal(writer=self.user1,
                                          game_attendance=self.char1_attendances[x],
                                          is_downtime=False)
            journal.set_content(VALID_JOURNAL_CONTENT)
            if x == 3:
                self.assertIsNotNone(journal.get_improvement())
                self.assertIsNone(journal.get_exp_reward())
            else:
                self.assertIsNone(journal.get_improvement())
                self.assertIsNotNone(journal.get_exp_reward())

    def test_downtimes_one_reward(self):
        journal = self.__make_journal(writer=self.user1,
                                      game_attendance=self.char1_attendances[0],
                                      is_downtime=False)
        journal.set_content(VALID_JOURNAL_CONTENT)
        for x in range(6):
            downtime_journal = self.__make_journal(writer=self.user1,
                                            game_attendance=self.char1_attendances[0],
                                          is_downtime=True)
            downtime_journal.set_content(VALID_JOURNAL_CONTENT)
        self.assertEquals(self.char1.num_unspent_improvements(), 0)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (2 * JOURNAL_EXP))

    def test_journals_void_rewards(self):
        journals = []
        for x in range(6):
            journal = self.__make_journal(writer=self.user1,
                                          game_attendance=self.char1_attendances[x],
                                          is_downtime=False)
            journal.set_content(VALID_JOURNAL_CONTENT)
            journals.append(journal)
        self.assertEquals(self.char1.num_unspent_improvements(), 1)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (5 * JOURNAL_EXP))
        exp_journal = journals[0]
        self.assertIsNone(exp_journal.get_improvement())
        self.assertIsNotNone(exp_journal.get_exp_reward())
        exp_journal.set_content(INVALID_JOURNAL_CONTENT)
        exp_journal.refresh_from_db()
        self.assertEquals(self.char1.num_unspent_improvements(), 1)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (4 * JOURNAL_EXP))
        self.assertIsNone(exp_journal.get_improvement())
        self.assertIsNone(exp_journal.get_exp_reward())
        exp_journal.set_content(VALID_JOURNAL_CONTENT)
        exp_journal.refresh_from_db()
        self.assertIsNone(exp_journal.get_improvement())
        self.assertIsNotNone(exp_journal.get_exp_reward())
        self.assertEquals(self.char1.num_unspent_improvements(), 1)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (5 * JOURNAL_EXP))

        improvement_journal = journals[3]
        self.assertIsNotNone(improvement_journal.get_improvement())
        self.assertIsNone(improvement_journal.get_exp_reward())
        improvement_journal.set_content(INVALID_JOURNAL_CONTENT)
        improvement_journal.refresh_from_db()
        self.assertIsNone(improvement_journal.get_improvement())
        self.assertIsNone(improvement_journal.get_exp_reward())
        self.assertEquals(self.char1.num_unspent_improvements(), 0)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (5 * JOURNAL_EXP))
        improvement_journal.set_content(VALID_JOURNAL_CONTENT)
        improvement_journal.refresh_from_db()
        self.assertIsNotNone(improvement_journal.get_improvement())
        self.assertIsNone(improvement_journal.get_exp_reward())
        self.assertEquals(self.char1.num_unspent_improvements(), 1)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (5 * JOURNAL_EXP))


        improvement_journal.set_content(INVALID_JOURNAL_CONTENT)
        improvement_journal.refresh_from_db()
        self.assertIsNone(improvement_journal.get_improvement())
        self.assertIsNone(improvement_journal.get_exp_reward())
        self.assertEquals(self.char1.num_unspent_improvements(), 0)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (5 * JOURNAL_EXP))

        journal = self.__make_journal(writer=self.user1,
                                      game_attendance=self.char1_attendances[7],
                                      is_downtime=False)
        journal.set_content(VALID_JOURNAL_CONTENT)
        journals.append(journal)
        self.assertIsNotNone(journal.get_improvement())
        self.assertIsNone(journal.get_exp_reward())
        self.assertEquals(self.char1.num_unspent_improvements(), 1)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (5 * JOURNAL_EXP))

    def test_journal_change_attendance(self):
        journals = []
        for x in range(6):
            journal = self.__make_journal(writer=self.user1,
                                          game_attendance=self.char1_attendances[x],
                                          is_downtime=False)
            journal.set_content(VALID_JOURNAL_CONTENT)
            journals.append(journal)
        exp_journal = journals[0]
        self.assertIsNone(exp_journal.get_improvement())
        self.assertIsNotNone(exp_journal.get_exp_reward())
        self.assertEquals(exp_journal.get_exp_reward().rewarded_character, self.char1)
        self.assertEquals(self.char1.num_unspent_improvements(), 1)

        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (12 * EXP_WIN) + (5 * JOURNAL_EXP))
        self.assertEquals(self.char2.exp_earned(), EXP_NEW_CHAR + (0 * EXP_WIN))
        exp_journal.game_attendance.change_outcome(new_outcome='WIN', is_confirmed=True, attending_character=self.char1)
        exp_journal.refresh_from_db()
        self.assertIsNone(exp_journal.get_improvement())
        self.assertIsNotNone(exp_journal.get_exp_reward())
        self.assertEquals(exp_journal.get_exp_reward().rewarded_character, self.char1)
        exp_journal.game_attendance.change_outcome(new_outcome='WIN', is_confirmed=True, attending_character=self.char2)
        exp_journal.refresh_from_db()
        self.assertEquals(self.char1.num_unspent_improvements(), 1)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (11 * EXP_WIN) + (4 * JOURNAL_EXP))
        self.assertEquals(self.char2.exp_earned(), EXP_NEW_CHAR + (1 * EXP_WIN) + JOURNAL_EXP)
        self.assertIsNone(exp_journal.get_improvement())
        self.assertIsNotNone(exp_journal.get_exp_reward())
        self.assertEquals(exp_journal.get_exp_reward().rewarded_character, self.char2)

        improvement_journal = journals[3]
        self.assertIsNotNone(improvement_journal.get_improvement())
        self.assertIsNone(improvement_journal.get_exp_reward())
        self.assertEquals(improvement_journal.get_improvement().rewarded_character, self.char1)

        improvement_journal.game_attendance.change_outcome(new_outcome='WIN', is_confirmed=True, attending_character=self.char1)
        improvement_journal.refresh_from_db()
        self.assertEquals(self.char1.num_unspent_improvements(), 1)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (11 * EXP_WIN) + (4 * JOURNAL_EXP))
        self.assertEquals(self.char2.exp_earned(), EXP_NEW_CHAR + (1 * EXP_WIN) + JOURNAL_EXP)
        self.assertIsNotNone(improvement_journal.get_improvement())
        self.assertIsNone(improvement_journal.get_exp_reward())
        self.assertEquals(improvement_journal.get_improvement().rewarded_character, self.char1)

        improvement_journal.game_attendance.change_outcome(new_outcome='WIN', is_confirmed=True, attending_character=self.char2)
        improvement_journal.refresh_from_db()
        self.assertIsNone(improvement_journal.get_improvement()) # it is char2s second journal. still no improvement rewarded
        self.assertIsNotNone(improvement_journal.get_exp_reward())
        self.assertEquals(improvement_journal.get_exp_reward().rewarded_character, self.char2)
        self.assertEquals(self.char1.num_unspent_improvements(), 0)
        self.assertEquals(self.char1.exp_earned(), EXP_NEW_CHAR + (10 * EXP_WIN) + (4 * JOURNAL_EXP))
        self.assertEquals(self.char2.exp_earned(), EXP_NEW_CHAR + (2 * EXP_WIN) + (2 * JOURNAL_EXP))


