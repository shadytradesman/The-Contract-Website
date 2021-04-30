from django.test import TestCase
from django.contrib.auth.models import User
from .signals import make_profile_for_new_user

class JournalModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')
        make_profile_for_new_user(None, self.user1)
        self.user2 = User.objects.create_user(
            username='jacob2', email='jacob@2…', password='top_secret')
        make_profile_for_new_user(None, self.user2)

    def test_no_nsfw_by_default(self):
        self.assertFalse(self.user1.profile.can_view_adult())
        self.assertFalse(self.user2.profile.can_view_adult())


    def test_change_perms(self):
        self.user1.profile.update_view_adult_content(True)
        self.assertTrue(self.user1.profile.can_view_adult())
        self.assertFalse(self.user2.profile.can_view_adult())

        self.user1.profile.update_view_adult_content(True)
        self.assertTrue(self.user1.profile.can_view_adult())

        self.user1.profile.update_view_adult_content(False)
        self.assertFalse(self.user1.profile.can_view_adult())

        self.user1.profile.update_view_adult_content(False)
        self.assertFalse(self.user1.profile.can_view_adult())

        self.user2.profile.update_view_adult_content(False)
        self.assertFalse(self.user2.profile.can_view_adult())
