from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.conf import settings

from .content_renderer import render_content

def get_pics_by_slug():
    pics_by_slug = {}
    for pic in GuidePic.objects.all():
        pics_by_slug[pic.slug] = pic
    return pics_by_slug

class GuideBook(models.Model):
    # A container for Guide Sections.
    title = models.CharField(max_length=400)
    slug = models.SlugField("Unique URL-Safe Title", max_length=80, primary_key=True)
    position = models.PositiveIntegerField(default=1) # determines position in dropdown menu and index
    expanded = models.BooleanField(default=False) # should this book be expanded in quick-access from navbar
    redirect_url = models.CharField(max_length=400, blank=True, null=True) # redirect to here instead of being viewable as a guidebook
    content = models.TextField(max_length=74000) # tinymce html content for editing
    rendered_content = models.TextField(max_length=74000)  # content that is rendered for display
    is_under_construction = models.BooleanField(default=False) # should we show an "under construction" banner at the top?

    def save(self, *args, **kwargs):
        self.rendered_content = render_content(self.content, get_pics_by_slug())
        super(GuideBook, self).save(*args, **kwargs)

    def get_sections_in_order(self, is_admin=False):
        sections = GuideSection.objects.filter(book=self, is_deleted=False)
        if not is_admin:
            sections = sections.filter(is_hidden=False)
        return sections.order_by('position').all()

    def get_url(self):
        return reverse('guide:read_guidebook', args=(self.slug,))


class GuideSection(models.Model):
    # Sections and subsections of a book.
    book = models.ForeignKey(GuideBook, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000) # Displayed title
    header_level = models.PositiveIntegerField(default=2) # Defines the sections "depth" in a hierarchical guide. 1-5
    slug = models.SlugField("URL-Safe Title", max_length=80) # must be unique per GuideBook
    position = models.PositiveIntegerField(default=1) # Guide sections are ordered by their position.
    is_deleted = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_spoilers = models.BooleanField(default=False)
    content = models.TextField(max_length=74000) # tinymce html content for editing
    rendered_content = models.TextField(max_length=78000) # content that is rendered for display
    last_editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    edit_date = models.DateTimeField('date last edited', null=True, blank=True)
    tags = models.JSONField(default=list) # Tags for searching through the guide.

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

    def save(self, *args, **kwargs):
        self.rendered_content = render_content(self.content, get_pics_by_slug())
        super(GuideSection, self).save(*args, **kwargs)

    def to_url(self):
        return "{}#{}".format(reverse('guide:read_guidebook', args=(self.book_id,)), self.slug)

    @staticmethod
    def section_to_url(book_id, slug):
        return "{}#{}".format(reverse('guide:read_guidebook', args=(book_id,)), slug)

class GuidePic(models.Model):
    slug = models.SlugField(primary_key=True)
    picture = models.ImageField()
