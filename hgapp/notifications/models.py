import datetime

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.templatetags.static import static
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


PLAYGROUP_NOTIF = "PLAYGROUP"
CONTRACT_NOTIF = "CONTRACT"
SCENARIO_NOTIF = "SCENARIO"
JOURNAL_NOTIF = "JOURNAL"
REWARD_NOTIF = "REWARD"
CONTRACTOR_NOTIF = "CONTRACTOR"
PROMOTIONAL_NOTIF = "PROMO"
WORLD_NOTIF = "WORLD"
MESSAGE_NOTIF = "MESSAGE"
ARTIFACT_NOTIF = "ARTIFACT"
NOTIFICATION_TYPE = (
    (PLAYGROUP_NOTIF, "Playgroup"),
    (CONTRACT_NOTIF, "Contract"),
    (SCENARIO_NOTIF, "Scenario"),
    (JOURNAL_NOTIF, "Journal"),
    (REWARD_NOTIF, "Reward"),
    (CONTRACTOR_NOTIF, "Contractor"),
    (PROMOTIONAL_NOTIF, "Promotional"),
    (WORLD_NOTIF, "World"),
    (MESSAGE_NOTIF, "Message"),
    (ARTIFACT_NOTIF, "Artifact"),
)


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    headline = models.CharField(max_length=3000)
    content = models.CharField(max_length=6000)
    url = models.CharField(max_length=3000)
    notif_type = models.CharField(choices=NOTIFICATION_TYPE, max_length=20)

    is_timeline = models.BooleanField(default=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.CharField(max_length=2000, blank=True)
    article = GenericForeignKey() # the world event, journal, etc. Must implement render_timeline_display()

    # an optional string for differentiating between two sorts of notifications for the same object.
    variety = models.CharField(max_length=2000, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_date']),
            models.Index(fields=['user', 'is_timeline', 'created_date']),
        ]

    @staticmethod
    def set(player):
        time = PlayerLastReadTime.get_last_read_for_player(player)
        return Notification.objects.filter(user=player, created_date__gt=time).order_by('-created_date')

    @staticmethod
    def get_timeline_notifications_for_player_queryset(player, max=15):
        return Notification.objects.filter(user=player, is_timeline=True).order_by('-created_date')[:max]

    @staticmethod
    def get_unread_notifications_for_player_queryset(player):
        time = PlayerLastReadTime.get_last_read_for_player(player)
        return Notification.objects.filter(user=player, created_date__gt=time).order_by('-created_date')

    @staticmethod
    def get_read_notifications_for_player_queryset(player, max=10):
        time = PlayerLastReadTime.get_last_read_for_player(player)
        return Notification.objects.filter(user=player, created_date__lt=time).order_by('-created_date')[:max]

    @staticmethod
    def get_num_unread_notifications_for_player(player):
        time = PlayerLastReadTime.get_last_read_for_player(player)
        return Notification.objects.filter(user=player, created_date__gt=time).count()

    def get_icon(self):
        notif_type = self.notif_type
        if notif_type == PLAYGROUP_NOTIF:
            return static("overrides/notif_icons/backup.svg")
        if notif_type == CONTRACT_NOTIF:
            return static("overrides/notif_icons/conqueror.svg")
        if notif_type == SCENARIO_NOTIF:
            return static("overrides/notif_icons/papers.svg")
        if notif_type == JOURNAL_NOTIF:
            return static("overrides/notif_icons/bookmarklet.svg")
        if notif_type == REWARD_NOTIF:
            return static("overrides/notif_icons/cash.svg")
        if notif_type == CONTRACTOR_NOTIF:
            return static("overrides/notif_icons/person.svg")
        if notif_type == PROMOTIONAL_NOTIF:
            return static("overrides/notif_icons/falling-star.svg")
        if notif_type == WORLD_NOTIF:
            return static("overrides/notif_icons/wireframe-globe.svg")
        if notif_type == MESSAGE_NOTIF:
            return static("overrides/notif_icons/envelope.svg")
        if notif_type == ARTIFACT_NOTIF:
            return static("overrides/notif_icons/power-ring.svg")


class PlayerLastReadTime(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    time_read = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    @staticmethod
    def get_last_read_for_player(player):
        time = PlayerLastReadTime.objects.filter(user=player).first()
        if time is None:
            return datetime.datetime(1970, 1, 1)
        else:
            return time.time_read

    @staticmethod
    def update_last_read_for_player(player):
        time = PlayerLastReadTime.objects.filter(user=player).first()
        if time is None:
            PlayerLastReadTime.objects.create(user=player)
        else:
            time.time_read = timezone.now()
            time.save()

