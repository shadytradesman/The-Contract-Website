from django.urls import path
from . import views

app_name = 'reporting'
urlpatterns = [
    path('content/<str:content_app>/<str:content_model>/<str:content_id>', views.ReportContent.as_view(), name='report_content'),
    # path('report/url/<path:reported_url>/', views.report_url, name='report_url'),

    path('moderation/queue', views.ModerationQueue.as_view(), name='moderation_queue'),
    path('moderation/queue/<int:report_id>', views.ModerationQueue.as_view(), name='moderation_queue'),

    #TODO:
    # Moderation queue
    # Previous reports
]
