from django.db import migrations, models
from django.db import transaction
from django.utils import timezone

NOT_PORTED = "NOT_PORTED"
SEASONED_PORTED = "SEASONED_PORTED"
VETERAN_PORTED = "VETERAN_PORTED"
PORT_STATUS = (
    (NOT_PORTED, "Not ported"),
    (SEASONED_PORTED, "Ported as Seasoned"),
    (VETERAN_PORTED, "Ported as Veteran"),
)

OLD_PORTED_GIFT_ADJUSTMENT = {
    NOT_PORTED: 0,
    SEASONED_PORTED: 15,
    VETERAN_PORTED: 30,
}

OLD_PORTED_IMPROVEMENT_ADJUSTMENT = {
    NOT_PORTED: 0,
    SEASONED_PORTED: 5,
    VETERAN_PORTED: 10,
}

PORTED_GIFT_ADJUSTMENT = {
    NOT_PORTED: 0,
    SEASONED_PORTED: 15,
    VETERAN_PORTED: 30,
}

PORTED_IMPROVEMENT_ADJUSTMENT = {
    NOT_PORTED: 0,
    SEASONED_PORTED: 13,
    VETERAN_PORTED: 20,
}

def migrate_ported_improvements(apps, schema_editor):
    Reward = apps.get_model('games', 'Reward')
    Character = apps.get_model('characters', 'Character')

    all_ported_characters = Character.objects.exclude(ported=NOT_PORTED).all()

    for character in all_ported_characters:
        with transaction.atomic():
            update_ported_rewards(character, Reward)


def update_ported_rewards(character, Reward):
    num_gifts = PORTED_GIFT_ADJUSTMENT[character.ported] - OLD_PORTED_GIFT_ADJUSTMENT[character.ported]
    num_improvements = PORTED_IMPROVEMENT_ADJUSTMENT[character.ported] - OLD_PORTED_IMPROVEMENT_ADJUSTMENT[character.ported]
    alterPortedRewards(Reward,
        character=character,
                       num_gifts=num_gifts,
                       num_improvements=num_improvements)


def alterPortedRewards(Reward, **kwargs):
    # voids or grants gifts based on the value of kwarg num_gifts
    character = kwargs["character"]
    num_gifts = kwargs["num_gifts"]
    num_improvements = kwargs["num_improvements"]
    if character.player:
        if num_gifts > 0:
            for x in range(num_gifts):
                reward = Reward(rewarded_player=character.player,
                                rewarded_character=character,
                                is_improvement=False,
                                is_ported_reward=True,
                                awarded_on = timezone.now())
                reward.save()
        elif num_gifts < 0:
            num_to_void = num_gifts * -1
            gifts_to_void = character.reward_set \
                                .filter(is_void=False, is_improvement=False, is_ported_reward=True) \
                                .all()[:num_to_void]
            for gift in gifts_to_void:
                mark_void(gift)
        if num_improvements > 0:
            for x in range(num_improvements):
                reward = Reward(rewarded_player=character.player,
                                rewarded_character=character,
                                is_improvement=True,
                                is_ported_reward=True,
                                awarded_on = timezone.now())
                reward.save()
        elif num_improvements < 0:
            num_to_void = num_improvements * -1
            improvements_to_void = character.reward_set \
                                       .filter(is_void=False, is_improvement=True, is_ported_reward=True) \
                                       .all()[:num_to_void]
            for improvement in improvements_to_void:
                mark_void(improvement)

def mark_void(self):
    self.is_void = True
    self.save()


def reverse_migrate_ported_rewards():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0056_auto_20230514_1542'),
    ]

    operations = [
        migrations.RunPython(migrate_ported_improvements, reverse_migrate_ported_rewards),
    ]
