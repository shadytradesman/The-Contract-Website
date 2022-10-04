from django.urls import path

from . import views


app_name = 'emails'
urlpatterns = [
    # path('preferences/<int:user_id>/<slug:secret_key>/', views.EmailPrefs.as_view(), name='email_preferences'),
]
