from django.core.management.base import BaseCommand, CommandError
from games.models import Game

class Command(BaseCommand):
    help = 'awards rewards for all games that don\'t have rewards awarded'

    def handle(self, *args, **options):
        for game in Game.objects.all():
            if game.reward_set.all().count() == 0:
                self.stdout.write("rewarding players for " + str(game.id))
                game.give_rewards()
        self.stdout.write(self.style.SUCCESS('Successfully awarded rewards for all games'))