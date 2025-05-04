from django.urls import re_path
from profiles.views import ProfileView, profile_edit, accept_terms, ProfileTimelineView

app_name = 'profiles'
urlpatterns = [
    # ex: .com/profile/view/21/
    re_path(r'^view/(?P<pk>[\d]+)/$', ProfileView.as_view(), name='profiles_view_profile'),

    # ex: .com/profile/view-timeline/21/
    re_path(r'^view-timeline/(?P<pk>[\d]+)/$', ProfileTimelineView.as_view(), name='profiles_timeline'),

    # ex: .com/profile/edit
    re_path(r'^edit/$', profile_edit, name='profiles_edit'),

    # ex: .com/profile/terms/
    re_path(r'^terms/$', accept_terms, name='profiles_terms'),
]