from django.test import TestCase
from django.urls import reverse

from .models import Base_Power, Base_Power_Category, ACTIVATION_STYLE


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
        default_activation_style = ACTIVATION_STYLE[1],
        is_public = public,
    )

class CreatePowerTests(TestCase):
    def test_public_powers_show_in_list_of_all(self):
        create_base_power(
            power_slug = "blast",
            base_power_category = create_base_power_category("Offense"),
            public = True)
        response = self.client.get(reverse('powers:create all'))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            ['<Base_Power:  (summary of base power)>']
        )

    def test_non_public_powers_do_not_show_in_list_of_all(self):
        create_base_power(
            power_slug="blast",
            base_power_category=create_base_power_category("Offense"),
            public=False)
        response = self.client.get(reverse('powers:create all'))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            []
        )

    def test_public_powers_show_in_list_by_cat(self):
        category_name = "Offense"
        create_base_power(
            power_slug="blast",
            base_power_category=create_base_power_category(category_name),
            public=True)
        response = self.client.get(reverse('powers:create category', args=(category_name,)))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            ['<Base_Power:  (summary of base power)>']
        )

    def test_non_public_powers_do_not_show_in_list_by_cat(self):
        category_name = "Offense"
        create_base_power(
            power_slug="blast",
            base_power_category=create_base_power_category(category_name),
            public=False)
        response = self.client.get(reverse('powers:create category', args=(category_name,)))
        self.assertQuerysetEqual(
            response.context['powers_list'],
            []
        )

