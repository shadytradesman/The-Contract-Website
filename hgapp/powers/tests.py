from django.test import TestCase, override_settings
from django.urls import reverse
import os
from powers.models import Base_Power, Base_Power_Category, PowerTutorial
import hgapp.settings

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
    PowerTutorial.objects.create(
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

def create_base_power(power_slug, base_power_category, public):
    return Base_Power.objects.create(
        slug = power_slug,
        category = base_power_category,
        summary = "summary of base power",
        description = "description of base power",
        eratta = "eratta of base power",
        is_public = public,
    )

class CreatePowerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        setup_tutorial()

    @override_settings(TEMPLATES=TEMPLATES)
    def test_public_powers_show_in_list_of_all(self):
        create_base_power(
            power_slug = "blast",
            base_power_category = create_base_power_category("Offense"),
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
            base_power_category=create_base_power_category("Offense"),
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
            base_power_category=create_base_power_category(category_name),
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
            base_power_category=create_base_power_category(category_name),
            public=False)
        response = self.client.get(reverse('powers:powers_create_category', args=(category_name,)))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            []
        )

