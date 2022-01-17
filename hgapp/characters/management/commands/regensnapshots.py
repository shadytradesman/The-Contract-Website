import logging

from django.core.management.base import BaseCommand, CommandError
from characters.models import Character
from django.db import transaction

logger = logging.getLogger("app." + __name__)

class Command(BaseCommand):
    help = 'regenerates all character stat snapshots'

    def handle(self, *args, **options):
        characters = Character.objects.all()
        successful = 0
        failure = 0
        for character in characters:
            try:
                with transaction.atomic():
                    character.regen_stats_snapshot()
                    successful = successful + 1
            except Exception as inst:
                logger.error('Error regenerating stats snapshot for character %s id %s',
                             str(character.name),
                             str(character.id))
                logger.exception(inst)
                failure = failure + 1
        self.stdout.write(self.style.SUCCESS('Regenerated snapshots. %d successful. %d failed.' % (successful, failure)))