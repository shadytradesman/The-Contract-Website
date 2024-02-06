from django.urls import path
from . import views

app_name = 'reporting'
urlpatterns = [
    path('report/content/<str:content_app>/<str:content_model>/<str:content_id>', views.ReportContent.as_view(), name='report_content'),
    # path('report/url/<path:reported_url>/', views.report_url, name='report_url'),

    #TODO:
    # Moderation queue
    # Previous reports
]
