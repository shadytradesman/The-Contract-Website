from django.conf.urls import url
from profiles.views import ProfileView, profile_edit, accept_terms, ProfileTimelineView

app_name = 'profiles'
urlpatterns = [
    # ex: .com/profile/view/21/
    url(r'^view/(?P<pk>[\d]+)/$', ProfileView.as_view(), name='profiles_view_profile'),

    # ex: .com/profile/view-timeline/21/
    url(r'^view-timeline/(?P<pk>[\d]+)/$', ProfileTimelineView.as_view(), name='profiles_timeline'),

    # ex: .com/profile/edit
    url(r'^edit/$', profile_edit, name='profiles_edit'),

    # ex: .com/profile/terms/
    url(r'^terms/$', accept_terms, name='profiles_terms'),
]