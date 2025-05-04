import django.dispatch

GrantAssetGift = django.dispatch.Signal() # providing_args=['assetDetail', 'character']
VoidAssetGifts = django.dispatch.Signal() # providing_args=['assetDetail', 'character']
AlterPortedRewards = django.dispatch.Signal() # providing_args=['character', 'num_gifts', 'num_improvements']
transfer_consumables = django.dispatch.Signal() # providing_args=['original_artifact', 'new_artifact', 'quantity', 'power']
recalculate_stats = django.dispatch.Signal() # providing_args=['character_pk', 'is_game']
