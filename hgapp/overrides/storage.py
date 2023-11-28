from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings as django_settings
from storages.utils import setting


class PrivateS3Storage(S3Boto3Storage):
    bucket_name = setting('AWS_STORAGE_PRIVATE_BUCKET_NAME')
    querystring_auth = True
