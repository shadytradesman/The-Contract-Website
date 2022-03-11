from django.conf.urls import url
from django.urls import path

from .views import BasePowerDetailView
from . import views

app_name = 'powers'
urlpatterns = [
    ### NEW POWER SYSTEM
    # ex: .com/powers/create-ps2/
    path('create-ps2/', views.CreatePower.as_view(), name='powers_create_ps2'),

    # ex: .com/powers/create-ps2/c/32
    path('create/c/<int:character_id>/', views.CreatePower.as_view(), name='powers_create_ps2_for_char'),

    # ex: .com/powers/edit-ps2/p/21
    path('edit-ps2/p/<int:power_full_id>/', views.EditExistingPower.as_view(), name='powers_edit_ps2'),

    # ex: .com/powers/edit-ps2/p/21
    path('create-ps2/p/<int:power_full_id>/', views.CreatePower.as_view(), name='powers_create_from_existing_ps2'),

    ### SHARED
    # ex: .com/powers/bases_and_examples/
    url(r'^bases_and_examples/$', views.powers_and_examples, name='powers_and_examples'),

    # ex: .com/powers/and-effects
    url(r'^and-effects/$', views.powers_and_effects, name='powers_and_effects'),

    # ex: .com/powers/delete/p/110
    url(r'^delete/p/(?P<power_id>[\d]+)/$', views.delete_power, name='powers_delete_power'),

    # ex: .com/powers/stock
    url(r'^stock/$', views.stock, name='powers_stock'),

    # ex: .com/powers/view/p/121
    path('view/p/<int:power_id>/', views.ViewPower.as_view(), name='powers_view_power'),

    # this url is useful for always showing the most recent version of a power
    # ex: .com/powers/view/history/p/121
    url(r'^view/history/p/(?P<power_full_id>[\d]+)/$', views.power_full_view, name='powers_view_power_full'),

    ### LEGACY POWER SYSTEM
    # ex: .com/powers/create/
    url(r'^create/$', views.create, name='powers_create'),

    # ex: .com/powers/create/c/32
    url(r'^create/c/(?P<character_id>[\d]+)$', views.create, name='powers_create_for_char'),

    # ex: .com/powers/create/offensive
    url(r'^create/cat/(?P<category_slug>[\w-]+)/$', views.create_category, name='powers_create_category'),

    # ex: .com/powers/create/offensive/c/12
    url(r'^create/cat/(?P<category_slug>[\w-]+)/c/(?P<character_id>[\d]+)$', views.create_category, name='powers_create_category_for_char'),

    # ex: .com/powers/create/all
    url(r'^create/all/$', views.create_all, name='powers_create_all'),

    # ex: .com/powers/create/all/c/21
    url(r'^create/all/c/(?P<character_id>[\d]+)$', views.create_all, name='powers_create_all_for_char'),

    # ex: .com/powers/create/b/blast
    url(r'^create/b/(?P<base_power_slug>[\w-]+)/$', views.create_power, name = 'powers_create_power'),

    # ex: .com/powers/create/b/blast/c/21
    url(r'^create/b/(?P<base_power_slug>[\w-]+)/c/(?P<character_id>[\d]+)$', views.create_power, name='powers_create_power_for_char'),

    # ex: .com/powers/create/p/110
    url(r'^create/p/(?P<power_id>[\d]+)/$', views.create_power_from_existing, name='powers_create_power_from_existing'),

    # ex: .com/powers/edit/p/110
    url(r'^edit/p/(?P<power_id>[\d]+)/$', views.edit_power, name='powers_edit_power'),

    # ex: .com/powers/view/b/blast
    url(r'^view/b/(?P<pk>[\w-]+)/$', BasePowerDetailView.as_view(), name='powers_view_base'),

]