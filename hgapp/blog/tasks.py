from celery import shared_task

from.models import Post

from profiles.models import Profile
from notifications.models import Notification, PROMOTIONAL_NOTIF
from emails.tasks import send_email_for_published_article


@shared_task(name="publish_article")
def publish_article(article_pk, url):
    article = Post.objects.get(pk=article_pk)
    profiles = Profile.objects.all()
    notif_headline = "Website Update"
    notif_content = article.title
    for profile in profiles:
        email = profile.get_confirmed_email()
        if profile.site_announcements==True and email is not None:
            send_email_for_published_article(email, article, url)
        Notification.objects.create(user=profile.user,
                                    headline=notif_headline,
                                    content=notif_content,
                                    url=url,
                                    notif_type=PROMOTIONAL_NOTIF,
                                    is_timeline=True,
                                    article=article,
                                    variety=article.section_id)
    return "Completed successfully"

