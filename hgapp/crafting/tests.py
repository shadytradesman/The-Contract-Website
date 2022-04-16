from django.test import TestCase
from django.contrib.auth.models import User
from crafting.models import CraftingEvent, CraftedArtifact
from characters.models import Character, ContractStats, Asset, Liability, AssetDetails, LiabilityDetails, Attribute, \
    AttributeValue, Ability, AbilityValue, Roll, NO_PARRY_INFO, NO_SPEED_INFO, UNAVOIDABLE, FREE_ACTION, TraumaRevision, \
    Trauma, NOT_PORTED, SEASONED_PORTED, VETERAN_PORTED, PORTED_GIFT_ADJUSTMENT, PORTED_IMPROVEMENT_ADJUSTMENT, \
    PORTED_EXP_ADJUSTMENT, EXP_NEW_CHAR, Artifact, GIVEN
from powers.models import Base_Power, Base_Power_Category, PowerTutorial, Power, EFFECT, VECTOR, MODALITY, SYS_PS2, \
    SYS_ALL, SYS_LEGACY_POWERS, CREATION_NEW, CRAFTING_CONSUMABLE, CRAFTING_NONE, Power_Full, PowerSystem
from django.db import transaction
from games.models import Reward, Scenario, Game, Game_Attendance, GAME_STATUS, WIN, Game_Invite
from cells.models import Cell
from profiles.signals import make_profile_for_new_user
from django.utils import timezone


def create_base_power_category(category_slug):
    return Base_Power_Category.objects.create(
        slug = category_slug,
        name = category_slug,
        description = category_slug
    )

def create_base_power(power_slug, category=None, public=True, type=EFFECT, crafting_type=CRAFTING_NONE):
    return Base_Power.objects.create(
        slug = power_slug,
        category = category,
        summary = "summary of base power",
        description = "description of base power",
        eratta = "eratta of base power",
        is_public = public,
        base_type=type,
        crafting_type=crafting_type,
    )

def create_power(system=SYS_PS2, effect=None, vector=None, modality=None, character=None):
    power = Power.objects.create(
        name="name",
        flavor_text="flavor",
        description="description",
        dice_system=system,
        base=effect,
        vector=vector,
        modality=modality,
        creation_reason=CREATION_NEW,)
    if character:
        power.character=character
        power.created_by=character.player
        power.save()
    new_power_full = Power_Full(
        name=power.name,
        dice_system=SYS_PS2,
        base=power.base,
        crafting_type=power.modality.crafting_type)
    if character:
        new_power_full.private = character.private
        new_power_full.character = character
        new_power_full.owner = character.player
    new_power_full.latest_rev = power
    new_power_full.save()
    power.parent_power = new_power_full
    power.save()
    return power

class CraftingModelTests(TestCase):
    def setUp(self):
        self.power_system = PowerSystem.objects.create()
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
        self.char2 = Character.objects.create(
            name="testchar",
            tagline="they test so well!",
            player=self.user2,
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
            notes="I guess it's good we have this field.")
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
        self.grant_basic_stats_to_char(self.char_full)
        self.grant_basic_stats_to_char(self.char2)
        self.category_name = "Offense"
        self.base_effect = create_base_power(
            power_slug="blast",
            category=create_base_power_category(self.category_name),
            public=True,
            type=EFFECT)
        self.base_vector = create_base_power(
            power_slug="direct",
            public=True,
            type=VECTOR)
        self.base_modality = create_base_power(
            power_slug="consumable-crafting",
            public=True,
            type=MODALITY,
            crafting_type=CRAFTING_CONSUMABLE)
        self.scenario = Scenario.objects.create(
            title="test scenario",
            summary="summary",
            description="blah",
            creator=self.user1,
            max_players=1,
            min_players=2)

    def send_contractor_on_game(self, character):
        game = Game(
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
        game.save()
        attendance = Game_Attendance(
            relevant_game=game,
            notes="notes",
            outcome=WIN,
            attending_character=character,
        )
        game_invite = Game_Invite(invited_player=character.player,
                                  relevant_game=game,
                                  as_ringer=False,
                                  )
        attendance.save()
        game_invite.attendance = attendance
        game_invite.save()
        game.give_rewards()
        return attendance

    def grant_basic_stats_to_char(self, char_full):
        stats_snapshot = ContractStats(assigned_character=char_full,
                                       is_snapshot=True)
        stats_snapshot.save()
        char_full.stats_snapshot = stats_snapshot
        char_full.save()
        stats_diff = ContractStats(assigned_character=char_full)
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
        char_full.regen_stats_snapshot()

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

    def test_basic_consumable_crafting_pre_game(self):
        power = create_power(effect=self.base_effect, vector=self.base_vector, modality=self.base_modality, character=self.char_full)
        original_exp = self.char_full.unspent_experience()
        crafting_event = CraftingEvent.objects.create(
            relevant_character=self.char_full,
            relevant_power=power,
            relevant_power_full=power.parent_power)

        crafting_event.craft_new_consumables(
            number_newly_crafted=3,
            exp_cost_per=1,
            new_number_free=1,
            power_full=power.parent_power)
        self.assertEquals(crafting_event.total_exp_spent, 2)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        new_artifact = self.char_full.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 3)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 2)
        self.assertTrue(new_artifact.is_consumable)
        self.assertFalse(new_artifact.is_signature)
        self.assertEquals(new_artifact.character, power.character)
        self.assertEquals(new_artifact.crafting_character, power.character)
        self.assertEquals(new_artifact.creating_player, power.character.player)
        self.assertIsNone(new_artifact.cell)

        crafting_event.craft_new_consumables(
            number_newly_crafted=1,
            exp_cost_per=1,
            new_number_free=0,
            power_full=power.parent_power)
        self.assertEquals(crafting_event.total_exp_spent, 3)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        new_artifact = self.char_full.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 4)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 3)

        power2 = create_power(effect=self.base_effect, vector=self.base_vector, modality=self.base_modality, character=self.char_full)
        crafting_event2 = CraftingEvent.objects.create(
            relevant_character=self.char_full,
            relevant_power=power2,
            relevant_power_full=power2.parent_power)
        crafting_event2.craft_new_consumables(
            number_newly_crafted=10,
            exp_cost_per=2,
            new_number_free=1,
            power_full=power2.parent_power)
        self.assertEquals(crafting_event2.total_exp_spent, 18)
        self.assertEquals(self.char_full.artifact_set.count(), 2)
        new_artifact2 = crafting_event2.artifacts.first()
        self.assertEquals(new_artifact2.quantity, 10)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 3 - 18)

        crafting_event2.craft_new_consumables(
            number_newly_crafted=3,
            exp_cost_per=2,
            new_number_free=3,
            power_full=power2.parent_power)
        self.assertEquals(crafting_event2.total_exp_spent, 18)
        self.assertEquals(self.char_full.artifact_set.count(), 2)
        new_artifact2 = crafting_event2.artifacts.first()
        self.assertEquals(new_artifact2.quantity, 13)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 3 - 18)

        crafting_event.refund_crafted_consumables(number_to_refund=3, exp_cost_per=1)
        # now there is only one crafted and it is free
        self.assertEquals(crafting_event.total_exp_spent, 0)
        self.assertEquals(self.char_full.artifact_set.count(), 2)
        new_artifact = crafting_event.artifacts.first()
        self.assertEquals(new_artifact.quantity, 1)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 18)

        # Too many to refund
        with transaction.atomic():
            with self.assertRaises(ValueError):
                crafting_event.refund_crafted_consumables(number_to_refund=3, exp_cost_per=1)

        new_artifact.quantity = 0 #used a consumable
        new_artifact.save()
        # we can still refund even if a consumable has been used.
        crafting_event.refund_crafted_consumables(number_to_refund=1, exp_cost_per=1)
        self.assertEquals(crafting_event.total_exp_spent, 0)
        self.assertEquals(self.char_full.artifact_set.count(), 2)
        new_artifact = crafting_event.artifacts.first()
        self.assertEquals(new_artifact.quantity, 0)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 18)

    def test_basic_consumable_crafting_after_game(self):
        power = create_power(effect=self.base_effect, vector=self.base_vector, modality=self.base_modality, character=self.char_full)
        attendance = self.send_contractor_on_game(self.char_full)

        original_exp = self.char_full.unspent_experience()
        crafting_event = CraftingEvent.objects.create(
            relevant_attendance=attendance,
            relevant_character=self.char_full,
            relevant_power=power,
            relevant_power_full=power.parent_power)

        crafting_event.craft_new_consumables(
            number_newly_crafted=3,
            exp_cost_per=1,
            new_number_free=1,
            power_full=power.parent_power)
        self.assertEquals(crafting_event.total_exp_spent, 2)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        new_artifact = self.char_full.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 3)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 2)

    def test_transfer_consumables(self):
        power = create_power(effect=self.base_effect, vector=self.base_vector, modality=self.base_modality, character=self.char_full)
        attendance = self.send_contractor_on_game(self.char_full)

        original_exp = self.char_full.unspent_experience()
        original_exp2 = self.char2.unspent_experience()
        crafting_event = CraftingEvent.objects.create(
            relevant_attendance=attendance,
            relevant_character=self.char_full,
            relevant_power=power,
            relevant_power_full=power.parent_power)

        crafting_event.craft_new_consumables(
            number_newly_crafted=3,
            exp_cost_per=1,
            new_number_free=1,
            power_full=power.parent_power)
        new_artifact = self.char_full.artifact_set.first()

        # try transfer too many
        with transaction.atomic():
            with self.assertRaises(ValueError):
                new_artifact.transfer_to_character(transfer_type=GIVEN, to_character=self.char2, notes="", quantity=5)

        # try transfer to self
        with transaction.atomic():
            with self.assertRaises(ValueError):
                new_artifact.transfer_to_character(transfer_type=GIVEN, to_character=self.char_full, notes="", quantity=1)

        self.assertEquals(crafting_event.total_exp_spent, 2)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        self.assertEquals(self.char2.artifact_set.count(), 0)
        self.assertEquals(new_artifact.quantity, 3)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 2)

        new_artifact.transfer_to_character(transfer_type=GIVEN, to_character=self.char2, notes="", quantity=1)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        self.assertEquals(self.char2.artifact_set.count(), 1)
        self.assertEquals(self.char2.unspent_experience(), original_exp2)
        new_artifact = self.char_full.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 2)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 2)

        new_artifact2 = self.char2.artifact_set.first()
        self.assertEquals(new_artifact2.quantity, 1)
        self.assertTrue(new_artifact2.is_consumable)
        self.assertFalse(new_artifact2.is_signature)
        self.assertEquals(new_artifact2.character, self.char2)
        self.assertEquals(new_artifact2.crafting_character, power.character)
        self.assertEquals(new_artifact2.creating_player, power.character.player)
        self.assertIsNone(new_artifact2.cell)

        new_artifact.transfer_to_character(transfer_type=GIVEN, to_character=self.char2, notes="", quantity=1)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        self.assertEquals(self.char2.artifact_set.count(), 1)
        new_artifact = self.char_full.artifact_set.first()
        new_artifact2 = self.char2.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 1)
        self.assertEquals(new_artifact2.quantity, 2)

        new_artifact2.transfer_to_character(transfer_type=GIVEN, to_character=self.char_full, notes="", quantity=2)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        self.assertEquals(self.char2.artifact_set.count(), 1)
        new_artifact = self.char_full.artifact_set.first()
        new_artifact2 = self.char2.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 3)
        self.assertEquals(self.char_full.unspent_experience(), original_exp - 2)
        self.assertEquals(new_artifact2.quantity, 0)
        self.assertTrue(new_artifact2.is_consumable)
        self.assertFalse(new_artifact2.is_signature)

        new_artifact.transfer_to_character(transfer_type=GIVEN, to_character=self.char2, notes="", quantity=1)
        self.assertEquals(self.char_full.artifact_set.count(), 1)
        self.assertEquals(self.char2.artifact_set.count(), 1)
        new_artifact = self.char_full.artifact_set.first()
        new_artifact2 = self.char2.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 2)
        self.assertEquals(new_artifact2.quantity, 1)

        crafting_event.refund_crafted_consumables(number_to_refund=2, exp_cost_per=1)
        new_artifact = self.char_full.artifact_set.first()
        new_artifact2 = self.char2.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 0)
        self.assertEquals(new_artifact2.quantity, 1)

        crafting_event.refund_crafted_consumables(number_to_refund=1, exp_cost_per=1)
        new_artifact = self.char_full.artifact_set.first()
        new_artifact2 = self.char2.artifact_set.first()
        self.assertEquals(new_artifact.quantity, 0)
        self.assertEquals(new_artifact2.quantity, 0)


    #TODO: Add tests for multiple games behavior, transfering / refunding stacks of artifacts that were produced in different events
    #TODO: Add tests for power refund, revision, etc.