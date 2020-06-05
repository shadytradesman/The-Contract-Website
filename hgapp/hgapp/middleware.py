import pytz

from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.user.is_superuser:
                tzname = request.user.account.timezone
                if tzname:
                    timezone.activate(pytz.timezone(tzname))
                else:
                    timezone.deactivate()
            else:
                timezone.deactivate()
        return self.get_response(request)