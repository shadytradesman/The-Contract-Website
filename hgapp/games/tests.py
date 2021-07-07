from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.db.utils import IntegrityError
from django.db import transaction
from characters.models import Character, ContractStats, Asset, Liability, AssetDetails, LiabilityDetails, Attribute, \
    AttributeValue, Ability, AbilityValue, ExperienceReward, EXP_NEW_CHAR, EXP_LOSS, EXP_WIN
from games.models import Game, Game_Attendance, Reward, Game_Invite, GAME_STATUS, OUTCOME, WIN, LOSS, DEATH, DECLINED, \
    RINGER_VICTORY, RINGER_FAILURE

from cells.models import Cell
from profiles.signals import make_profile_for_new_user
from django.utils import timezone

def make_test_char(player, cell=None):
    return Character.objects.create(
            name="testchar",
            tagline="they test so well!",
            player=player,
            appearance="they're sexy because that's better.",
            age="131 years",
            sex="applebees",
            concept_summary="unique but unrelatable",
            ambition="collect all original ramones recordings",
            private=False,
            pub_date=timezone.now(),
            edit_date=timezone.now(),
            cell = cell,
            notes="I guess it's good we have this field.")

class GameModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')
        make_profile_for_new_user(None, self.user1)
        self.user2 = User.objects.create_user(
            username='jacob2', email='jacob@2…', password='top_secret')
        make_profile_for_new_user(None, self.user2)
        self.cell_owner = User.objects.create_user(
            username='jacob23', email='jacob@23…', password='top_secret')
        make_profile_for_new_user(None, self.cell_owner)
        self.cell = Cell.objects.create(
                            name = "cell name",
                            creator = self.cell_owner,
                            setting_name = "world name",
                            setting_description = "Test description")
        self.setup_stat_elements()
        self.char_user1_cell = make_test_char(self.user1, self.cell)
        self.char_user1_cell2 = make_test_char(self.user1, self.cell)
        self.char_user2_cell = make_test_char(self.user2, self.cell)
        self.char_user2_nocell = make_test_char(self.user2)
        self.char_cellowner_cell = make_test_char(self.cell_owner, self.cell)
        self.grant_basic_stats_to_char(self.char_user1_cell)
        self.grant_basic_stats_to_char(self.char_user1_cell2)
        self.grant_basic_stats_to_char(self.char_user2_cell)
        self.grant_basic_stats_to_char(self.char_user2_nocell)
        self.grant_basic_stats_to_char(self.char_cellowner_cell)

    def setup_stat_elements(self):
        self.liability = Liability.objects.create(
            name="lame",
            value=2,
            description="blah",
            system="blah",
            details_field_name="deets",
            multiplicity_allowed=False,
        )
        self.asset = Asset.objects.create(
            name="strong",
            value=1,
            description="blah",
            system="blah",
            details_field_name="deets",
            multiplicity_allowed=False,
        )
        self.attribute_str = Attribute.objects.create(
            name="str",
            tutorial_text="tut"
        )
        self.ability = Ability.objects.create(
            name="athletics",
            tutorial_text="tut"
        )
        
    def grant_basic_stats_to_char(self, char):
        stats_snapshot = ContractStats(assigned_character=char,
                                       is_snapshot=True)
        stats_snapshot.save()
        char.stats_snapshot = stats_snapshot
        char.save()
        stats_diff = ContractStats(assigned_character=char)
        stats_diff.save()
        AssetDetails.objects.create(
            details="original deets",
            relevant_stats=stats_diff,
            relevant_asset=self.asset
        )
        LiabilityDetails.objects.create(
            details="original deets",
            relevant_stats=stats_diff,
            relevant_liability=self.liability
        )
        AttributeValue.objects.create(
            value=3,
            relevant_stats=stats_diff,
            relevant_attribute=self.attribute_str,
        )
        AbilityValue.objects.create(
            value=2,
            relevant_stats=stats_diff,
            relevant_ability=self.ability,
        )
        char.regen_stats_snapshot()


    def test_archive_game_victory(self):
        self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
        self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
        self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
        self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
        self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
        self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
        game = Game(
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
        game.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=WIN,
            attending_character=self.char_user1_cell,
        )
        game_invite = Game_Invite(invited_player=self.user1,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        game.give_rewards()
        self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 1)
        self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 1)
        self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
        self.assertEquals(self.char_user1_cell.number_of_victories(), 1)
        self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
        self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_WIN)

    def test_archive_game_loss(self):
        self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
        self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
        self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
        self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
        self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
        self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
        game = Game(
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
        game.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=LOSS,
            attending_character=self.char_user1_cell,
        )
        game_invite = Game_Invite(invited_player=self.user1,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        game.give_rewards()
        self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
        self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
        self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
        self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
        self.assertEquals(self.char_user1_cell.number_of_losses(), 1)
        self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_LOSS)

    def test_archive_game_death(self):
        self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
        self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
        self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
        self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
        self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
        self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
        self.assertEquals(
            self.user1.rewarded_player
                .filter(rewarded_character=None, is_charon_coin=True)
                .filter(is_void=False).all().count(),
            0)
        game = Game(
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
        game.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=OUTCOME[2][0], # death
            attending_character=self.char_user1_cell,
        )
        game_invite = Game_Invite(invited_player=self.user1,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        game.give_rewards()
        self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
        self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
        self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
        self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
        self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
        self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
        self.assertEquals(self.char_user1_cell.is_dead(), True)
        self.assertEquals(
            self.user1.rewarded_player
                .filter(rewarded_character=None, is_charon_coin=True)
                .filter(is_void=False).all().count(),
            1)

    def test_archive_game_gm_rewards_basic(self):
        self.assertEquals(self.user2.experiencereward_set.filter(rewarded_character=None).all().count(), 0)
        self.assertEquals(self.user2.rewarded_player.filter(rewarded_character=None, is_charon_coin=False).filter(is_void=False).all().count(), 0)
        self.assertEquals(
            self.user1.rewarded_player
                .filter(rewarded_character=None, is_charon_coin=True)
                .filter(is_void=False).all().count(),
            0)
        game = Game(
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
        game.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=DEATH,
            attending_character=self.char_user1_cell,
        )
        game_invite = Game_Invite(invited_player=self.user1,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        game.give_rewards()
        self.assertEquals(self.user2.experiencereward_set.filter(rewarded_character=None).all().count(), 1)
        self.assertEquals(self.user2.rewarded_player.filter(rewarded_character=None, is_charon_coin=False, is_new_player_gm_reward=False).filter(is_void=False).all().count(), 0)
        self.assertEquals(
            self.user1.rewarded_player
                .filter(rewarded_character=None, is_charon_coin=True)
                .filter(is_void=False).all().count(),
            1)

    def test_archive_game_gm_rewards_ratio(self):
        self.assertEquals(self.user2.experiencereward_set.filter(rewarded_character=None).all().count(), 0)
        self.assertEquals(
            self.user2.rewarded_player.filter(rewarded_character=None, is_charon_coin=False).filter(is_void=False).all().count(), 0)

        game = Game(
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
        game.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=WIN,
            attending_character=self.char_user1_cell,
        )
        game_invite = Game_Invite(invited_player=self.user1,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=DEATH,
            attending_character=self.char_cellowner_cell,
        )
        game_invite = Game_Invite(invited_player=self.cell_owner,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        game.give_rewards()
        self.assertEquals(self.user2.experiencereward_set.filter(rewarded_character=None).all().count(), 1)
        self.assertEquals(self.user2.rewarded_player.filter(rewarded_character=None, is_charon_coin=False).filter(is_void=False).all().count(), 1)

    def test_archive_game_victory_not_in_cell(self):
        self.assertEquals(self.char_user2_nocell.unspent_rewards().count(), 0)
        self.assertEquals(self.char_user2_nocell.unspent_gifts().count(), 0)
        self.assertEquals(self.char_user2_nocell.completed_games().count(), 0)
        self.assertEquals(self.char_user2_nocell.number_of_victories(), 0)
        self.assertEquals(self.char_user2_nocell.number_of_losses(), 0)
        self.assertEquals(self.char_user2_nocell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user2_nocell.exp_earned(), EXP_NEW_CHAR)
        self.assertEquals(self.user2.game_invite_set.filter(attendance__is_confirmed=False).exclude(is_declined=True).all().count(), 0)
        game = Game(
            title="title",
            creator=self.user1,
            gm=self.user1,
            created_date=timezone.now(),
            scheduled_start_time=timezone.now(),
            actual_start_time=timezone.now(),
            end_time=timezone.now(),
            status=GAME_STATUS[6][0],
            cell=self.cell,
        )
        game.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=OUTCOME[0][0], # victory
            attending_character=self.char_user2_nocell,
            is_confirmed = False,
        )
        game_invite = Game_Invite(invited_player=self.user2,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        game.give_rewards()
        self.assertEquals(self.char_user2_nocell.unspent_rewards().count(), 0)
        self.assertEquals(self.char_user2_nocell.unspent_gifts().count(), 0)
        self.assertEquals(self.char_user2_nocell.completed_games().count(), 0)
        self.assertEquals(self.char_user2_nocell.number_of_victories(), 0)
        self.assertEquals(self.char_user2_nocell.number_of_losses(), 0)
        self.assertEquals(self.char_user2_nocell.stats_snapshot.sources.count(), 0)
        self.assertEquals(self.char_user2_nocell.exp_earned(), EXP_NEW_CHAR)
        self.assertEquals(self.user2.game_invite_set.filter(attendance__is_confirmed=False).exclude(is_declined=True).all().count(), 1)

    def test_cannot_double_invite(self):
        game = Game(
            title="title",
            creator=self.user1,
            gm=self.user1,
            created_date=timezone.now(),
            scheduled_start_time=timezone.now(),
            actual_start_time=timezone.now(),
            end_time=timezone.now(),
            status=GAME_STATUS[6][0],
            cell=self.cell,
        )
        game.save()
        game_invite = Game_Invite(invited_player=self.user2,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        game_invite.save()
        game_invite2 = Game_Invite(invited_player=self.user2,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        with self.assertRaises(IntegrityError):
            game_invite2.save()

    def test_archive_game_change_outcome(self):
        with transaction.atomic():
            game = Game(
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
            game.save()
            attendance = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=WIN,
                attending_character=self.char_user1_cell,
            )
            game_invite = Game_Invite(invited_player=self.user1,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            game.give_rewards()
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 1)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 1)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 1)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_WIN)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome = LOSS, is_confirmed = True)
            self.char_user1_cell.refresh_from_db()

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 1)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_LOSS)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome = WIN, is_confirmed = True)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 1)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 1)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 1)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_WIN)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome = DEATH, is_confirmed = True)

            self.assertEquals(self.char_user1_cell.is_dead(), True)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 1)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=DECLINED, is_confirmed=True)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1) #Maybe this should be different?
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=RINGER_VICTORY, is_confirmed=True)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 1)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 1)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=RINGER_FAILURE, is_confirmed=True)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=WIN, is_confirmed=True, attending_character=self.char_user1_cell)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 1)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 1)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 1)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_WIN)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)


    def test_archive_game_change_attending(self):
        with transaction.atomic():
            game = Game(
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
            game.save()
            attendance = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=WIN,
                attending_character=self.char_user1_cell,
            )
            game_invite = Game_Invite(invited_player=self.user1,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            game.give_rewards()
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 1)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 1)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 1)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_WIN)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome = WIN, is_confirmed = True, attending_character = self.char_user1_cell2)
            self.char_user1_cell.refresh_from_db()

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.char_user1_cell2.is_dead(), False)
            self.assertEquals(self.char_user1_cell2.unspent_rewards().count(), 1)
            self.assertEquals(self.char_user1_cell2.unspent_gifts().count(), 1)
            self.assertEquals(self.char_user1_cell2.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell2.number_of_victories(), 1)
            self.assertEquals(self.char_user1_cell2.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell2.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell2.exp_earned(), EXP_NEW_CHAR + EXP_WIN)

            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1) # New player reward
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1) # User 2 gmed the game

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome = RINGER_VICTORY, is_confirmed = True)
            # We switched the character to one owned by user2, so now user2 gets the rewards

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.char_user1_cell2.is_dead(), False)
            self.assertEquals(self.char_user1_cell2.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell2.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell2.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell2.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell2.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 1)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 1)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1)
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1) # User 2 gmed the game

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=DEATH, is_confirmed=True, attending_character=self.char_user1_cell)

            self.assertEquals(self.char_user1_cell.is_dead(), True)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.char_user1_cell2.is_dead(), False)
            self.assertEquals(self.char_user1_cell2.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell2.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell2.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell2.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell2.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 1)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1) #new player
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1) # User 2 gmed the game

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=DEATH, is_confirmed=True, attending_character=self.char_user1_cell2)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.char_user1_cell2.is_dead(), True)
            self.assertEquals(self.char_user1_cell2.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell2.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell2.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell2.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell2.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell2.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 1)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1) #new player
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1) # User 2 gmed the game

    def test_archive_game_change_attendance_confirmed(self):
        with transaction.atomic():
            game = Game(
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
            game.save()
            attendance = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=WIN,
                attending_character=self.char_user1_cell,
            )
            game_invite = Game_Invite(invited_player=self.user1,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            game.give_rewards()
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 1)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 1)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 1)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR + EXP_WIN)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome = WIN, is_confirmed = False, attending_character = self.char_user1_cell2)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.char_user1_cell2.is_dead(), False)
            self.assertEquals(self.char_user1_cell2.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell2.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell2.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell2.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell2.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1) # New Player attended
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1) # User 2 gmed the game

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=WIN, is_confirmed=True, attending_character=self.char_user1_cell2)

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.char_user1_cell2.is_dead(), False)
            self.assertEquals(self.char_user1_cell2.unspent_rewards().count(), 1)
            self.assertEquals(self.char_user1_cell2.unspent_gifts().count(), 1)
            self.assertEquals(self.char_user1_cell2.completed_games().count(), 1)
            self.assertEquals(self.char_user1_cell2.number_of_victories(), 1)
            self.assertEquals(self.char_user1_cell2.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell2.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell2.exp_earned(), EXP_NEW_CHAR + EXP_WIN)

            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1)
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1)  # User 2 gmed the game

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome = RINGER_VICTORY, is_confirmed = False)
            # We switched the character to one owned by user2, so now user2 gets the rewards

            self.assertEquals(self.char_user1_cell.is_dead(), False)
            self.assertEquals(self.char_user1_cell.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.char_user1_cell2.is_dead(), False)
            self.assertEquals(self.char_user1_cell2.unspent_rewards().count(), 0)
            self.assertEquals(self.char_user1_cell2.unspent_gifts().count(), 0)
            self.assertEquals(self.char_user1_cell2.completed_games().count(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_victories(), 0)
            self.assertEquals(self.char_user1_cell2.number_of_losses(), 0)
            self.assertEquals(self.char_user1_cell2.stats_snapshot.sources.count(), 0)
            self.assertEquals(self.char_user1_cell2.exp_earned(), EXP_NEW_CHAR)

            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1) #new player
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1) # User 2 gmed the game

            attendance.refresh_from_db()
            attendance.change_outcome(new_outcome=RINGER_VICTORY, is_confirmed=True)
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 1)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 1)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 1)
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 1) # User 2 gmed the game

    def test_archive_game_recalculate_golden_ratio(self):
        with transaction.atomic():
            game = Game(
                title="title",
                creator=self.user2,
                gm=self.cell_owner,
                created_date=timezone.now(),
                scheduled_start_time=timezone.now(),
                actual_start_time=timezone.now(),
                end_time=timezone.now(),
                status=GAME_STATUS[6][0],
                cell=self.cell,
            )
            game.save()
            attendance = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=WIN,
                attending_character=self.char_user1_cell,
            )
            game_invite = Game_Invite(invited_player=self.user1,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            game.give_rewards()
            self.assertFalse(game.achieves_golden_ratio())
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_improvements().count(), 1) # new player
            self.assertEquals(self.cell_owner.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_exp_rewards().count(), 1) # cell_owner gmed the game

            attendance2 = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=DEATH,
                attending_character=self.char_user2_cell,
            )
            game_invite = Game_Invite(invited_player=self.user2,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance2.save()
            game_invite.attendance = attendance2
            game_invite.save()
            attendance2.give_reward()
            game.refresh_from_db()
            game.recalculate_gm_reward(False)

            self.assertTrue(game.achieves_golden_ratio())
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 1) # from dying
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.cell_owner.profile.get_avail_improvements().count(), 1) # from ratio
            self.assertEquals(self.cell_owner.profile.get_avail_improvements().first().is_new_player_gm_reward, False) # ratio reward
            self.assertEquals(self.cell_owner.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_exp_rewards().count(), 1)  # cell_owner gmed the game

            attendance2.refresh_from_db()
            attendance2.change_outcome(new_outcome=WIN, is_confirmed=True)
            game.refresh_from_db()
            game.recalculate_gm_reward(True)

            self.assertFalse(game.achieves_golden_ratio())
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 0)

            self.assertEquals(self.cell_owner.profile.get_avail_improvements().count(), 1) # no more ratio reward
            self.assertEquals(self.cell_owner.profile.get_avail_improvements().first().is_new_player_gm_reward, True) # no more ratio reward
            self.assertEquals(self.cell_owner.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_exp_rewards().count(), 1)  # cell_owner gmed the game

    def test_no_new_player_reward_for_not_new_players(self):
        with transaction.atomic():
            game = Game(
                title="title",
                creator=self.cell_owner,
                gm=self.cell_owner,
                created_date=timezone.now(),
                scheduled_start_time=timezone.now(),
                actual_start_time=timezone.now(),
                end_time=timezone.now(),
                status=GAME_STATUS[6][0],
                cell=self.cell,
            )
            game.save()
            attendance = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=WIN,
                attending_character=self.char_user1_cell,
            )
            game_invite = Game_Invite(invited_player=self.user1,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            game.give_rewards()
            self.assertFalse(game.achieves_golden_ratio())
            self.assertEquals(self.user1.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user1.profile.get_avail_exp_rewards().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_improvements().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.user2.profile.get_avail_exp_rewards().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_improvements().count(), 1) # new player
            self.assertEquals(self.cell_owner.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_exp_rewards().count(), 1) # cell_owner gmed the game

            game = Game(
                title="title",
                creator=self.cell_owner,
                gm=self.cell_owner,
                created_date=timezone.now(),
                scheduled_start_time=timezone.now(),
                actual_start_time=timezone.now(),
                end_time=timezone.now(),
                status=GAME_STATUS[6][0],
                cell=self.cell,
            )
            game.save()
            attendance = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=WIN,
                attending_character=self.char_user1_cell,
            )
            game_invite = Game_Invite(invited_player=self.user1,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            game.give_rewards()

            self.assertEquals(self.cell_owner.profile.get_avail_improvements().count(), 1) # only one new player reward
            self.assertEquals(self.cell_owner.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_exp_rewards().count(), 2) # cell_owner gmed the game

            game = Game(
                title="title",
                creator=self.cell_owner,
                gm=self.cell_owner,
                created_date=timezone.now(),
                scheduled_start_time=timezone.now(),
                actual_start_time=timezone.now(),
                end_time=timezone.now(),
                status=GAME_STATUS[6][0],
                cell=self.cell,
            )
            game.save()
            attendance = Game_Attendance(
                relevant_game=game,
                notes="notes",
                outcome=WIN,
                attending_character=self.char_user2_cell,
            )
            game_invite = Game_Invite(invited_player=self.user2,
                                      relevant_game=game,
                                      as_ringer=False,
                                      )
            attendance.save()
            game_invite.attendance = attendance
            game_invite.save()
            game.give_rewards()

            self.assertEquals(self.cell_owner.profile.get_avail_improvements().count(), 2) # user2's first game
            self.assertEquals(self.cell_owner.profile.get_avail_charon_coins().count(), 0)
            self.assertEquals(self.cell_owner.profile.get_avail_exp_rewards().count(), 3) # cell_owner gmed the game
