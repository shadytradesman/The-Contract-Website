import logging

from django.core.management.base import BaseCommand, CommandError
from characters.models import Character, ContractStats
from django.db import transaction

logger = logging.getLogger("app." + __name__)

class Command(BaseCommand):
    help = 'Grants elements for all existing assets and liabilities on Contractors.'

    def handle(self, *args, **options):
        characters = Character.objects.all()
        successful = 0
        failure = 0
        for character in characters:
            try:
                with transaction.atomic():
                    new_stats_rev = ContractStats(assigned_character=character)
                    new_stats_rev.save()

                    assets = character.stats_snapshot.assetdetails_set.all()
                    for asset in assets:
                        elem = asset.relevant_asset.grant_element_if_needed(new_stats_rev, asset.details)
                        elem.save()

                    liabilities = character.stats_snapshot.liabilitydetails_set.all()
                    for liability in liabilities:
                        elem = liability.relevant_liability.grant_element_if_needed(new_stats_rev, liability.details)
                        elem.save()

                    new_stats_rev.save()
                    character.regen_stats_snapshot()
                    successful = successful + 1
                    logger.info('Finished character %s id %s',
                                 str(character.name),
                                 str(character.id))
                    self.stdout.write(
                        self.style.SUCCESS('Finished character %s id %s' % (character.name, character.id)))
            except Exception as inst:
                logger.error('Error regenerating stats snapshot for character %s id %s',
                             str(character.name),
                             str(character.id))
                logger.exception(inst)
                failure = failure + 1
        self.stdout.write(self.style.SUCCESS('Regenerated snapshots. %d successful. %d failed.' % (successful, failure)))