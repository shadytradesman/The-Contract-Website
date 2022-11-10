from django.conf.urls import url
from django.urls import path

from .views import BasePowerDetailView
from django.views.generic.base import RedirectView

from . import views

app_name = 'powers'
urlpatterns = [
    ### NEW POWER SYSTEM
    # ex: .com/gift/create/
    path('create/', views.CreatePower.as_view(), name='powers_create_ps2'),
    path('create-ps2/', RedirectView.as_view(pattern_name='powers:powers_create_ps2', query_string=True, permanent=True)),

    # ex: .com/gift/create/for-contractor/32
    path('create/for-contractor/<int:character_id>/', views.CreatePower.as_view(), name='powers_create_ps2_for_char'),
    path('create-ps2/c/<int:character_id>/', RedirectView.as_view(pattern_name='powers:powers_create_ps2_for_char', query_string=True, permanent=True)),

    # ex: .com/gift/edit/21
    path('edit/<int:power_full_id>/', views.EditExistingPower.as_view(), name='powers_edit_ps2'),
    path('edit-ps2/p/<int:power_full_id>/', RedirectView.as_view(pattern_name='powers:powers_edit_ps2', query_string=True, permanent=True)),

    # ex: .com/gift/create/from-existing/21
    path('create/from-existing/<int:power_full_id>/', views.CreatePower.as_view(), name='powers_create_from_existing_ps2'),
    path('create/from-existing/<int:power_full_id>/c/<int:character_id>/', views.CreatePower.as_view(), name='powers_create_from_existing_ps2'),
    path('create-ps2/p/<int:power_full_id>/',
         RedirectView.as_view(pattern_name='powers:powers_create_from_existing_ps2', query_string=True, permanent=True)),

    # ex: .com/powers/toggle-active/p/21/off/
    path('toggle-active/p/<int:power_id>/<is_currently_active>/', views.toggle_active, name='powers_toggle_active'),
    # ex: .com/powers/toggle-active/p/21/off/a/21
    path('toggle-active/p/<int:power_id>/<is_currently_active>/a/<int:art_id>/', views.toggle_active, name='powers_toggle_active'),

    ### SHARED
    # ex: .com/gift/bases_and_examples/
    url(r'^example-audit/$', views.powers_and_examples, name='powers_and_examples'),

    # ex: .com/gift/and-effects
    url(r'^and-effects/$', views.powers_and_effects, name='powers_and_effects'),

    # ex: .com/gift/delete/110
    url(r'^delete/(?P<power_id>[\d]+)/$', views.delete_power, name='powers_delete_power'),
    url(r'^delete/p/(?P<power_id>[\d]+)/$',
         RedirectView.as_view(pattern_name='powers:powers_delete_power', query_string=True, permanent=True)),

    # ex: .com/gift/stock
    url(r'^stock/$', views.stock, name='powers_stock'),
    # ex: .com/gift/stock/c/56
    path('stock/c/<int:character_id>/', views.stock, name='powers_stock'),

    # View a revision of a gift
    # ex: .com/powers/view/p/121
    path('revision/<int:power_id>/', views.ViewPower.as_view(), name='powers_view_power'),
    path('view/p/<int:power_id>/',
         RedirectView.as_view(pattern_name='powers:powers_view_power', query_string=True, permanent=True)),

    # this url is useful for always showing the most recent version of a power
    # ex: .com/powers/view/history/p/121
    url(r'^(?P<power_full_id>[\d]+)/$', views.power_full_view, name='powers_view_power_full'),
    url(r'^view/history/p/(?P<power_full_id>[\d]+)/$',
         RedirectView.as_view(pattern_name='powers:powers_view_power_full', query_string=True, permanent=True)),

    ### AJAX ENDPOINTS
    path('ajax/example/effect/<slug:effect_id>/', views.ajax_example_view, name='powers_view_power_full_ajax'),

    ### LEGACY POWER SYSTEM
    # ex: .com/powers/create/
    url(r'^create-legacy/$', views.create, name='powers_create'),

    # ex: .com/powers/create/c/32
    url(r'^create-legacy/c/(?P<character_id>[\d]+)$', views.create, name='powers_create_for_char'),

    # ex: .com/powers/create/offensive
    url(r'^create-legacy/cat/(?P<category_slug>[\w-]+)/$', views.create_category, name='powers_create_category'),

    # ex: .com/powers/create/offensive/c/12
    url(r'^create-legacy/cat/(?P<category_slug>[\w-]+)/c/(?P<character_id>[\d]+)$', views.create_category, name='powers_create_category_for_char'),

    # ex: .com/powers/create/all
    url(r'^create-legacy/all/$', views.create_all, name='powers_create_all'),

    # ex: .com/powers/create/all/c/21
    url(r'^create-legacy/all/c/(?P<character_id>[\d]+)$', views.create_all, name='powers_create_all_for_char'),

    # ex: .com/powers/create/b/blast
    url(r'^create-legacy/b/(?P<base_power_slug>[\w-]+)/$', views.create_power, name = 'powers_create_power'),

    # ex: .com/powers/create/b/blast/c/21
    url(r'^create-legacy/b/(?P<base_power_slug>[\w-]+)/c/(?P<character_id>[\d]+)$', views.create_power, name='powers_create_power_for_char'),

    # ex: .com/powers/create/p/110
    url(r'^create-legacy/p/(?P<power_id>[\d]+)/$', views.create_power_from_existing, name='powers_create_power_from_existing'),

    # ex: .com/powers/edit/p/110
    url(r'^edit-legacy/p/(?P<power_id>[\d]+)/$', views.edit_power, name='powers_edit_power'),

    # ex: .com/powers/view/b/blast
    url(r'^view-legacy/b/(?P<pk>[\w-]+)/$', BasePowerDetailView.as_view(), name='powers_view_base'),

]