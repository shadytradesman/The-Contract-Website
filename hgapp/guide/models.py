from django.db import models
from django.db.models import Q
from django.conf import settings


class GuideBook(models.Model):
    # A container for Guide Sections.
    title = models.CharField(max_length=400)
    slug = models.SlugField("Unique URL-Safe Title", max_length=80, primary_key=True)


class GuideSection(models.Model):
    # Sections and subsections of a book.
    book = models.ForeignKey(GuideBook, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000) # Displayed title
    header_level = models.PositiveIntegerField(default=2) # Defines the sections "depth" in a hierarchical guide. 1-5
    slug = models.SlugField("URL-Safe Title", max_length=80) # must be unique per GuideBook
    position = models.PositiveIntegerField(default=1) # Guide sections are ordered by their position.
    is_deleted = models.BooleanField(default=False)
    content = models.TextField(max_length=74000) # tinymce html content for editing
    rendered_content = models.TextField(max_length=78000) # content that is rendered for display
    last_editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    edit_date = models.DateTimeField('date last edited', null=True, blank=True)

    class Meta:
        constraints = [
            # two GuideSections in the same GuideBook cannot have the same slug.
            models.UniqueConstraint(fields=['book', 'slug'], condition=Q(is_deleted=False), name='one_slug_per_book'),
            # two GuideSections in the same GuideBook cannot have the same position.
            models.UniqueConstraint(fields=['book', 'position'], condition=Q(is_deleted=False), name='one_pos_per_book'),
        ]
        indexes = [
            models.Index(fields=['book', 'slug', 'is_deleted']),
            models.Index(fields=['book', 'position', 'is_deleted']),
            models.Index(fields=['position']),
        ]


    #Render text on save. Replaces
    # {{article-slug}} with link to that article
    # {{fancy-section}} with entire section
