import django.dispatch
GrantAssetGift = django.dispatch.Signal(providing_args=['assetDetail', 'character'])
VoidAssetGifts = django.dispatch.Signal(providing_args=['assetDetail', 'character'])