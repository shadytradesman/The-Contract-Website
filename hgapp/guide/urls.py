from django.urls import path


from . import views

app_name = 'guide'
urlpatterns = [
    # ex: .com/guide/rules/
    # ex: .com/guide/rules/#attributes
    path('<slug:guidebook_slug>/',
         views.ReadGuideBook.as_view(),
         name='read_guidebook'),

    # ex: .com/guide/edit/rules/attributes/
    path('edit/<slug:guidebook_slug>/<slug:section_slug>/',
         views.EditGuideSection.as_view(),
         name='edit_guide_section'),

    # ex: .com/guide/edit/rules/attributes/
    path('edit/<slug:guidebook_slug>/',
         views.EditGuidebook.as_view(),
         name='edit_guidebook'),

    # ex: .com/guide/add-new/rules/attributes/
    path('add-new/<slug:guidebook_slug>/<slug:section_slug>/',
         views.WriteNewGuideSection.as_view(),
         name='new_guide_section'),

    # ex: .com/guide/add-new/rules/
    path('add-new/<slug:guidebook_slug>/',
         views.WriteNewGuideSection.as_view(),
         name='new_guide_section'),

    # ex: .com/guide/delete/rules/attributes/
    path('delete/<slug:guidebook_slug>/<slug:section_slug>/',
         views.DeleteGuideSection.as_view(),
         name='delete_guide_section'),
]
