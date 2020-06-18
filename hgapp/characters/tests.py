from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from characters.models import Character
from cells.models import Cell
from django.utils import timezone

class CellModelTests(TestCase):
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


