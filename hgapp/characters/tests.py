from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from characters.models import Character, ContractStats, Asset, Liability, AssetDetails, LiabilityDetails, Attribute, \
    AttributeValue, Ability, AbilityValue, Roll
from games.models import Reward
from cells.models import Cell
from django.utils import timezone
from django.db.utils import IntegrityError
from django.db import transaction


class CharacterModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')
        self.user2 = User.objects.create_user(
            username='jacob2', email='jacob@2…', password='top_secret')
        self.cell_owner = User.objects.create_user(
            username='jacob23', email='jacob@23…', password='top_secret')
        self.cell = Cell.objects.create(
                            name = "cell name",
                            creator = self.cell_owner,
                            setting_name = "world name",
                            setting_description = "Test description")
        self.char_full = Character.objects.create(
            name="testchar",
            tagline="they test so well!",
            player=self.user1,
            appearance="they're sexy because that's better.",
            age="131 years",
            sex="applebees",
            concept_summary="unique but unrelatable",
            ambition="collect all original ramones recordings",
            private=False,
            pub_date=timezone.now(),
            edit_date=timezone.now(),
            cell = self.cell,
            paradigm = "what is this field",
            residence="wonkaland",
            languages="N/A",
            insanities="probably not a PC word",
            disabilities="none. They're op",
            current_alias="the candyman",
            previous_aliases="bjork, FDR",
            resources="No thank you",
            contacts="They know Elvis",
            equipment="This field is generally long, but they go naked.",
            total_encumbrance="we should calculate this",
            max_encumbrance="I mean this",
            wish_list="warf piece",
            to_do_list="go to a concert",
            contracts="this is very confusing given our system name",
            background="discovering this is the fun part!",
            notes="I guess it's good we have this field.")
        self.char_reqs = Character.objects.create(
            name="testchar2",
            tagline="they test so bad!",
            player=self.user2,
            appearance="they're ugly because that's better.",
            age="13 years",
            sex="taco bell",
            concept_summary="generic but relatable",
            ambition="eat a dragon's heart",
            private=True,
            pub_date=timezone.now(),
            edit_date=timezone.now(),
            cell=self.cell)
        self.liability = Liability.objects.create(
            name="lame",
            value=2,
            description="blah",
            system = "blah",
            details_field_name="deets",
            multiplicity_allowed = False,
        )
        self.asset = Asset.objects.create(
            name="strong",
            value=1,
            description="blah",
            system = "blah",
            details_field_name="deets",
            multiplicity_allowed = False,
        )
        self.attribute_str = Attribute.objects.create(
            name="str",
            tutorial_text="tut"
        )
        self.ability = Ability.objects.create(
            name="athletics",
            tutorial_text="tut"
        )

    def grant_basic_stats_to_char_full(self):
        stats_snapshot = ContractStats(assigned_character=self.char_full,
                                       is_snapshot=True)
        stats_snapshot.save()
        self.char_full.stats_snapshot = stats_snapshot
        self.char_full.save()
        stats_diff = ContractStats(assigned_character=self.char_full)
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
        self.char_full.regen_stats_snapshot()

    def reward_user(self, user):
        normal_reward = Reward(
            rewarded_character=self.char_full,
            rewarded_player=user,
            is_improvement=False,
            is_charon_coin=False,
            awarded_on=timezone.now(),
        )
        normal_reward.save()
        gm_reward = Reward(
            rewarded_player=user,
            is_improvement=True,
            is_charon_coin=False,
            awarded_on=timezone.now(),
        )
        gm_reward.save()
        coin_reward = Reward(
            rewarded_player=user,
            is_improvement=False,
            is_charon_coin=True,
            awarded_on=timezone.now(),
        )
        coin_reward.save()
        coin_reward = Reward(
            rewarded_player=user,
            is_improvement=False,
            is_charon_coin=True,
            awarded_on=timezone.now(),
        )
        coin_reward.save()

    def test_basic_privacy(self):
        self.assertTrue(self.char_full.player_can_view(self.user1))
        self.assertTrue(self.char_full.player_can_view(self.user2))
        self.assertFalse(self.char_reqs.player_can_view(self.user1))
        self.assertTrue(self.char_reqs.player_can_view(self.user2))

    def test_basic_death_and_void(self):
        self.char_full.kill()
        self.assertTrue(self.char_full.is_dead())
        self.assertEquals(len(self.char_full.void_deaths()), 0)
        self.assertTrue(self.char_full.real_death())
        death = self.char_full.real_death()
        death.is_void = True
        death.save()
        self.assertFalse(self.char_full.is_dead())
        self.assertEquals(len(self.char_full.void_deaths()), 1)
        self.assertFalse(self.char_full.real_death())
        self.char_full.kill()
        self.assertTrue(self.char_full.is_dead())
        self.assertEquals(len(self.char_full.void_deaths()), 1)
        self.assertNotEquals(self.char_full.real_death().id, death.id)

    def test_never_die_twice(self):
        self.char_full.kill()
        with self.assertRaises(ValueError):
            self.char_full.kill()

    def test_stats_base(self):
        self.grant_basic_stats_to_char_full()
        stats = self.char_full.stats_snapshot
        self.assertEquals(stats.assetdetails_set.all().count(), 1)
        self.assertEquals(stats.assetdetails_set.all()[0].details, "original deets")
        self.assertEquals(stats.liabilitydetails_set.all().count(), 1)
        self.assertEquals(stats.attributevalue_set.all().count(), 1)
        self.assertEquals(stats.abilityvalue_set.all().count(), 1)

    def test_stats_snapshot_assets(self): #TODO: test liabilities, traits, etc.
        self.grant_basic_stats_to_char_full()

        stats_diff = ContractStats(assigned_character=self.char_full)
        stats_diff.save()
        new_deets = AssetDetails.objects.create(
            details="new_details",
            relevant_stats=stats_diff,
            relevant_asset=self.asset,
            previous_revision=self.char_full.stats_snapshot.assetdetails_set.all()[0].previous_revision
        )
        new_deets.save()
        stats_diff.save()
        self.char_full.regen_stats_snapshot()
        self.assertEquals(self.char_full.stats_snapshot.assetdetails_set.all().count(), 1)
        self.assertEquals(self.char_full.stats_snapshot.assetdetails_set.all()[0].details, "new_details")

        stats_diff2 = ContractStats(assigned_character=self.char_full)
        stats_diff2.save()
        even_newer_deets = AssetDetails.objects.create(
            details="newer_details",
            relevant_stats=stats_diff2,
            relevant_asset=self.asset,
            previous_revision=new_deets
        )
        even_newer_deets.save()
        self.char_full.regen_stats_snapshot()
        self.assertEquals(self.char_full.stats_snapshot.assetdetails_set.all().count(), 1)
        self.assertEquals(self.char_full.stats_snapshot.assetdetails_set.all()[0].details, "newer_details")

        stats_history = self.char_full.contractstats_set.filter(is_snapshot=False).order_by("created_time").all()
        self.assertEquals(stats_history.count(), 3)
        snapshots = self.char_full.contractstats_set.filter(is_snapshot=True).all()
        self.assertEquals(snapshots.count(), 1)

    def test_stats_snapshot_assets_history(self):
        self.grant_basic_stats_to_char_full()

        stats_diff = ContractStats(assigned_character=self.char_full)
        stats_diff.save()
        new_deets = AssetDetails.objects.create(
            details="new_details",
            relevant_stats=stats_diff,
            relevant_asset=self.asset,
            previous_revision=self.char_full.stats_snapshot.assetdetails_set.all()[0].previous_revision
        )
        new_deets.save()
        stats_diff.save()
        self.char_full.regen_stats_snapshot()

        stats_diff2 = ContractStats(assigned_character=self.char_full)
        stats_diff2.save()
        even_newer_deets = AssetDetails.objects.create(
            details="newer_details",
            relevant_stats=stats_diff2,
            relevant_asset=self.asset,
            previous_revision=new_deets
        )
        even_newer_deets.save()
        self.char_full.regen_stats_snapshot()

        stats_history = self.char_full.contractstats_set.filter(is_snapshot=False).order_by("created_time").all()
        self.assertEquals(stats_history[0].assetdetails_set.all()[0].details, "original deets")
        self.assertEquals(stats_history[1].assetdetails_set.all()[0].details, "new_details")
        self.assertEquals(stats_history[2].assetdetails_set.all()[0].details, "newer_details")
        og_deets = stats_history[2].assetdetails_set.all()[0].previous_revision.previous_revision
        self.assertEquals(stats_history[0].assetdetails_set.all()[0].id, og_deets.id)
        snapshots = self.char_full.contractstats_set.filter(is_snapshot=True).all()
        self.assertEquals(snapshots.count(), 1)

    def test_stats_snapshot_assets_delete(self):
        self.grant_basic_stats_to_char_full()

        stats_diff = ContractStats(assigned_character=self.char_full)
        stats_diff.save()
        new_deets = AssetDetails.objects.create(
            details="new_details",
            relevant_stats=stats_diff,
            relevant_asset=self.asset,
            previous_revision=self.char_full.stats_snapshot.assetdetails_set.all()[0].previous_revision,
            is_deleted=True,
        )
        new_deets.save()
        stats_diff.save()
        self.char_full.regen_stats_snapshot()
        self.assertEquals(self.char_full.stats_snapshot.assetdetails_set.all().count(), 0)

        stats_diff2 = ContractStats(assigned_character=self.char_full)
        stats_diff2.save()
        even_newer_deets = AssetDetails.objects.create(
            details="newer_details",
            relevant_stats=stats_diff2,
            relevant_asset=self.asset,
        )
        even_newer_deets.save()
        self.char_full.regen_stats_snapshot()
        self.assertEquals(self.char_full.stats_snapshot.assetdetails_set.all().count(), 1)
        self.assertEquals(self.char_full.stats_snapshot.assetdetails_set.all()[0].details, "newer_details")

        stats_history = self.char_full.contractstats_set.filter(is_snapshot=False).order_by("created_time").all()
        self.assertEquals(stats_history.count(), 3)
        snapshots = self.char_full.contractstats_set.filter(is_snapshot=True).all()
        self.assertEquals(snapshots.count(), 1)

    def test_traits_and_quirks_cannot_have_snapshot_prev_rev(self):
        self.grant_basic_stats_to_char_full()
        stats_diff = ContractStats(assigned_character=self.char_full)
        stats_diff.save()
        with self.assertRaises(ValueError):
            AssetDetails.objects.create(
                details="new_details",
                relevant_stats=stats_diff,
                relevant_asset=self.asset,
                previous_revision=self.char_full.stats_snapshot.assetdetails_set.all()[0],
                is_deleted=True,
            )
        with self.assertRaises(ValueError):
            AttributeValue.objects.create(
                value=1,
                relevant_stats=stats_diff,
                relevant_attribute=self.attribute_str,
                previous_revision=self.char_full.stats_snapshot.attributevalue_set.all()[0],
            )

    def test_cannot_clear_stats_revision(self):
        stats_diff = ContractStats(assigned_character=self.char_full)
        stats_diff.save()
        with self.assertRaises(ValueError):
            stats_diff.clear()

    def test_stats_clear(self):
        self.grant_basic_stats_to_char_full()
        snapshot = self.char_full.stats_snapshot
        snapshot.clear()
        self.assertEquals(snapshot.assetdetails_set.all().count(), 0)
        self.assertEquals(snapshot.liabilitydetails_set.all().count(), 0)
        self.assertEquals(snapshot.abilityvalue_set.all().count(), 0)
        self.assertEquals(snapshot.attributevalue_set.all().count(), 0)

    def test_charon_coins(self):
        self.grant_basic_stats_to_char_full()
        self.reward_user(self.user1)
        self.assertFalse(self.char_full.assigned_coin())
        self.char_full.use_charon_coin()
        self.assertEquals(self.char_full.reward_set.filter(is_void=False, is_charon_coin=True).all().count(), 1)
        self.assertTrue(self.char_full.assigned_coin())
        self.char_full.use_charon_coin()
        self.assertEquals(self.char_full.reward_set.filter(is_void=False, is_charon_coin=True).all().count(), 1)
        self.assertTrue(self.char_full.assigned_coin())
        self.char_full.refund_coin()
        self.assertEquals(self.char_full.reward_set.filter(is_void=False, is_charon_coin=True).all().count(), 0)
        self.assertFalse(self.char_full.assigned_coin())
        self.char_full.refund_coin()



            #TEST TODOS
        # character.unspent_experience()
        # stats.exp_cost()
        # stats history
        # stats revisioning
        # stats revision exp cost
        # stats snapshot accuracy
        # GM game experience reward
        # Play in game experience reward
        # void game experience repo
        # void game gm experience repo

class RollModelTests(TestCase):
    def setUp(self):
        self.attribute_1 = Attribute.objects.create(
            name="str",
            tutorial_text="tut"
        )
        self.attribute_2 = Attribute.objects.create(
            name="dex",
            tutorial_text="tut"
        )
        self.ability_1 = Ability.objects.create(
            name="athletics",
            tutorial_text="tut"
        )
        self.ability_2 = Ability.objects.create(
            name="meditation",
            tutorial_text="tut"
        )

    def make_roll(self, attribute=None, ability=None, is_mind=False, is_body=False, difficulty=6):
        Roll.objects.create(
            attribute=attribute,
            ability=ability,
            is_mind=is_mind,
            is_body=is_body,
            difficulty=difficulty)

    def test_save_valid_rolls(self):
        self.make_roll(self.attribute_1, self.ability_1)
        self.make_roll(self.attribute_2, self.ability_1)
        self.make_roll(self.attribute_2, self.ability_2)
        self.make_roll(self.attribute_1, self.ability_1, difficulty=5)
        self.make_roll(is_mind=True)
        self.make_roll(is_body=True)
        self.assertEquals(Roll.objects.count(), 6)

    def test_no_duplicate_rolls(self):
        self.make_roll(self.attribute_1, self.ability_1)
        self.assertEquals(Roll.objects.count(), 1)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(self.attribute_1, self.ability_1)
        self.make_roll(self.attribute_1, self.ability_1, difficulty=5)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(self.attribute_1, self.ability_1, difficulty=5)
        self.assertEquals(Roll.objects.count(), 2)

    def test_only_one_mind_roll(self):
        self.make_roll(self.attribute_1, self.ability_1)
        self.make_roll(is_mind=True)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(is_mind=True)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(self.attribute_1, self.ability_1, is_mind=True)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(self.attribute_1, self.ability_2, is_mind=True)

    def test_only_one_body_roll(self):
        self.make_roll(self.attribute_1, self.ability_1)
        self.make_roll(is_body=True)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(is_body=True)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(self.attribute_1, self.ability_1, is_body=True)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.make_roll(self.attribute_1, self.ability_2, is_body=True)