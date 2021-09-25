import django.dispatch
GrantAssetGift = django.dispatch.Signal(providing_args=['assetDetail', 'character'])
VoidAssetGifts = django.dispatch.Signal(providing_args=['assetDetail', 'character'])
AlterPortedRewards = django.dispatch.Signal(providing_args=['character', 'num_gifts', 'num_improvements'])