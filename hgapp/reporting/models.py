from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

REASON_OBSCENE = "OBSCENE"
REASON_DOX = "DOX"
REASON_HARASSMENT = "HARASSMENT"
REASON_ADVERTISING = "ADVERTISING"
REASON_SPAM = "SPAM"
REASON_OTHER = "OTHER"
REPORT_REASON = (
    (REASON_OBSCENE, "Obscene or explicit content"),
    (REASON_DOX, "Sharing personal information"),
    (REASON_HARASSMENT, "Abuse or harassment"),
    (REASON_ADVERTISING, "Unsolicited advertising or sales"),
    (REASON_SPAM, "Spam"),
    (REASON_OTHER, "Other (specify below)"),
)

ACTION_DISMISSED = "DISMISSED"
ACTION_WARN = "WARNING"
ACTION_BAN = "BAN"
MODERATION_ACTION = (
    (ACTION_DISMISSED, "No Action"),
    (ACTION_WARN, "Warned"),
    (ACTION_BAN, "Banned"),
)

# Whitelist for reportable content. Should prevent people from arbitrarily probing the DB for any app/model.
ALLOWED_CONTENT_APPS = [
    "images",
]

ALLOWED_CONTENT_MODELS = [
    "userimage",
    "privateuserimage",
]


class Report(models.Model):
    reporting_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reporting_user")
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reported_user")
    created_date = models.DateTimeField(auto_now_add=True)

    reason = models.CharField(choices=REPORT_REASON, max_length=50)
    extended_reason = models.TextField(max_length=6000, blank=True) # user provided report text

    # url always uniquely identifies the content reported, even if content is null or it is not a clickable url
    # clickable urls begin with '/'
    # content reports will have this populated by get_absolute_url() if available, otherwise a hash of content fields
    url = models.CharField(max_length=3000)

    # the reported content, any type referenced must implement the following methods:
    # render_for_report()
    #       Render a snippet displaying the content for the moderation pages.
    # report_remove()
    #       Delete the offending content (or equivalent).
    # get_responsible_user()
    #       Returns the user responsible for uploading this content.
    #
    # They may optionally implement the following methods:
    # player_can_view(user)
    #       Return True/False if specified user can view the content. Users cannot report content they cannot view
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    content_id = models.CharField(max_length=2000, blank=True, null=True)
    content = GenericForeignKey('content_type', 'content_id')

    # Moderation state. Each report may be re-actioned by site moderators if the decision changes, but ideally a new
    # report is opened.
    moderation_reason = models.CharField(choices=REPORT_REASON, max_length=50, blank=True, null=True)
    moderation_date = models.DateTimeField(blank=True, null=True)
    moderating_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="moderating_user")
    moderation_action = models.CharField(choices=MODERATION_ACTION, max_length=50, blank=False, null=True)
    moderator_feedback = models.TextField(max_length=6000, blank=True, null=True)

    class Meta:
        unique_together = (
            ("reporting_user", "url")
        )
        indexes = [
            models.Index(fields=['moderation_date', 'url']),
            models.Index(fields=['created_date']),
            models.Index(fields=['reported_user', 'created_date']),
            models.Index(fields=['reported_user', 'moderation_action']),
        ]

    def is_unresolved(self):
        return self.moderation_date is None

    def moderate_warn(self):
        if not self.is_unresolved():
            raise ValueError("Cannot action on a resolved report")
