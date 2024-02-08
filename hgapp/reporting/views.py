from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction
from collections import defaultdict
from notifications.models import Notification, MESSAGE_NOTIF

from .utilities import ensure_content_type_is_reportable, ensure_content_object_is_reportable, get_url_for_content
from .forms import ReportForm, ModerationActionForm
from .models import Report, ACTION_DISMISSED, ACTION_BAN, ACTION_WARN
from profiles.models import Profile

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class ReportContent(View):
    template_name = 'reporting/report_content.html'
    content_app = None
    content_model = None
    content_id = None
    content_type = None
    content_object = None

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            raise ValueError("Must be logged in to report")

        self.content_app = self.kwargs["content_app"]
        self.content_model = self.kwargs["content_model"]
        self.content_id = self.kwargs["content_id"]
        self.content_type = ContentType.objects.get(app_label=self.content_app, model=self.content_model)
        ensure_content_type_is_reportable(content_type=self.content_type)

        self.content_object = self.content_type.get_object_for_this_type(pk=self.content_id)
        ensure_content_object_is_reportable(content_object=self.content_object)

        if hasattr(self.content_object, "player_can_view"):
            if not self.content_object.player_can_view(self.request.user):
                raise PermissionDenied("You cannot report content you cannot view")

        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                self.content_object = self.content_type.model_class().objects.select_for_update()\
                    .get(id=self.content_object.pk)
                new_report = form.save(commit=False)
                new_report.reporting_user = request.user
                new_report.reported_user = self.content_object.get_responsible_user()
                new_report.url = get_url_for_content(self.content_object, content_type=self.content_type)
                new_report.content = self.content_object
                new_report.save()
                moderators = Profile.objects.filter(is_site_moderator=True).all()
                for mod in moderators:
                    Notification.objects.create(user=mod.user,
                                                headline="New report",
                                                content="{} has been reported".format(new_report.reported_user.username),
                                                url=reverse("reporting:moderation_queue"),
                                                notif_type=MESSAGE_NOTIF)
        else:
            raise ValueError("Invalid form")

        # Redirect back to reporting page if available
        nxt = request.GET.get("next", None)
        if nxt is None:
            return redirect(settings.ACCOUNT_LOGIN_REDIRECT_URL)
        elif not url_has_allowed_host_and_scheme(
                url=nxt,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()):
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            return redirect(nxt)

    def __get_context_data(self):
        form = ReportForm()
        return {
            "form": form,
            "content_object": self.content_object,
            "url": self.request.GET.get("next", None),
        }


@method_decorator(login_required(login_url='account_login'), name='dispatch')
class ModerationQueue(View):
    template_name = 'reporting/moderation_queue.html'
    report = None

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            raise ValueError("Must be logged in to report")
        if not self.request.user.profile.is_site_moderator and not self.request.user.is_superuser:
            raise PermissionDenied("You cannot view the moderation queue")
        if "report_id" in kwargs:
            self.report = Report.objects.get(pk=kwargs["report_id"])
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = ModerationActionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if hasattr(self.report, "content") and self.report.content is not None:
                    content_object = self.report.content_type.model_class().objects.select_for_update().get(id=self.report.content_id)

                    # settle all existing reports
                    mod_action = form.cleaned_data['moderation_action']
                    mod_date = timezone.now()
                    Report.objects.filter(url=self.report.url, moderation_date__isnull=True)\
                        .update(moderation_date=mod_date,
                                moderation_action=mod_action,
                                moderation_reason=form.cleaned_data['moderation_reason'],
                                moderating_user=request.user,
                                moderator_feedback=form.cleaned_data['moderator_feedback'])

                    if mod_action != ACTION_DISMISSED:
                        content_object.report_remove()

                    # ban user if required
                    if self.report.reported_user.is_superuser == False and self.report.reported_user.profile.is_site_moderator == False:
                        num_warnings = Report.objects.filter(reported_user=self.report.reported_user,
                                                             moderation_action=ACTION_WARN)\
                            .distinct("moderation_date")\
                            .count()
                        if mod_action == ACTION_BAN or num_warnings > 2:
                            self.report.reported_user.is_active = False
                            self.report.reported_user.save()
        return redirect(reverse('reporting:moderation_queue'))

    def __get_context_data(self):
        all_reports = Report.objects.filter(moderation_date__isnull=True).order_by("url").all()
        reports_by_subject = defaultdict(list)
        for report in all_reports:
            reports_by_subject[report.url].append(report)
        closed_reports = Report.objects.filter(moderation_date__isnull=False).distinct("moderation_date").order_by("-moderation_date").all()
        return {
            "reports_by_subject": dict(reports_by_subject),
            "form": ModerationActionForm(),
            "closed_reports": closed_reports,
        }
