from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
import os
from powers.models import Base_Power, Base_Power_Category, PowerTutorial, Power, EFFECT, VECTOR, MODALITY, SYS_PS2,\
    SYS_ALL, SYS_LEGACY_POWERS, CREATION_NEW
from django.db.utils import IntegrityError

PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
#Required to render our templates using sekizai, tho we don't do that any more so we should revisit.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [
            os.path.join(PACKAGE_ROOT, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            "debug": True,
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "account.context_processors.account",
                "postman.context_processors.inbox",
            ],
        },
    },
]

def setup_tutorial():
    return PowerTutorial.objects.create(
        modal_base="nada",
        modal_base_header = "any",
        modal_edit_header = "what",
        modal_edit = "huh",
    )

def create_base_power_category(category_slug):
    return Base_Power_Category.objects.create(
        slug = category_slug,
        name = category_slug,
        description = category_slug
    )

def create_base_power(power_slug, category=None, public=True, type=EFFECT):
    return Base_Power.objects.create(
        slug = power_slug,
        category = category,
        summary = "summary of base power",
        description = "description of base power",
        eratta = "eratta of base power",
        is_public = public,
        base_type=type,
    )

def create_power(system=SYS_PS2, effect=None, vector=None, modality=None, created_by=None):
    return Power.objects.create(
        name="name",
        flavor_text="flavor",
        description="description",
        dice_system=system,
        base=effect,
        vector=vector,
        modality=modality,
        creation_reason=CREATION_NEW,)

class CreatePowerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        setup_tutorial()

    @override_settings(TEMPLATES=TEMPLATES)
    def test_public_powers_show_in_list_of_all(self):
        create_base_power(
            power_slug = "blast",
            category = create_base_power_category("Offense"),
            public = True)
        response = self.client.get(reverse('powers:powers_create_all'))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            ['<Base_Power:  (summary of base power)>']
        )

    @override_settings(TEMPLATES=TEMPLATES)
    def test_non_public_powers_do_not_show_in_list_of_all(self):
        create_base_power(
            power_slug="blast",
            category=create_base_power_category("Offense"),
            public=False)
        response = self.client.get(reverse('powers:powers_create_all'))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            []
        )

    @override_settings(TEMPLATES=TEMPLATES)
    def test_public_powers_show_in_list_by_cat(self):
        category_name = "Offense"
        create_base_power(
            power_slug="blast",
            category=create_base_power_category(category_name),
            public=True)
        response = self.client.get(reverse('powers:powers_create_category', args=(category_name,)))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            ['<Base_Power:  (summary of base power)>']
        )

    @override_settings(TEMPLATES=TEMPLATES)
    def test_non_public_powers_do_not_show_in_list_by_cat(self):
        category_name = "Offense"
        create_base_power(
            power_slug="blast",
            category=create_base_power_category(category_name),
            public=False)
        response = self.client.get(reverse('powers:powers_create_category', args=(category_name,)))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            []
        )

class PowerModelTests(TestCase):
    def setUp(self):
        self.tutorial = setup_tutorial()
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
            power_slug="power",
            public=True,
            type=MODALITY)
        self.user1 = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')

    def test_power_constraints(self):
        # successful
        create_power(effect=self.base_effect, vector=self.base_vector)
        create_power(modality=self.base_modality)

        # wrong effect type
        with self.assertRaises(IntegrityError):
            create_power(effect=self.base_vector, vector=self.base_vector)
        # wrong vector type
        with self.assertRaises(IntegrityError):
            create_power(effect=self.base_effect, vector=self.base_effect)
        # wrong modality type
        with self.assertRaises(IntegrityError):
            create_power(modality=self.base_effect)
        # can't set all three
        with self.assertRaises(IntegrityError):
            create_power(modality=self.base_modality, vector=self.base_vector, effect=self.base_effect)

