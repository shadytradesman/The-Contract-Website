from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.template import loader
import re


class GuideBook(models.Model):
    # A container for Guide Sections.
    title = models.CharField(max_length=400)
    slug = models.SlugField("Unique URL-Safe Title", max_length=80, primary_key=True)
    position = models.PositiveIntegerField(default=1) # determines position in dropdown menu and index
    expanded = models.BooleanField(default=False) # should this book be expanded in quick-access from navbar
    redirect_url = models.CharField(max_length=400, blank=True, null=True) # redirect to here instead of being viewable as a guidebook

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
        self.rendered_content = self.__render_content()
        super(GuideSection, self).save(*args, **kwargs)

    # Support for "STML" or Spencer Text Markup Language
    # This is a super-janky markup language that is intended only for admin use.
    # DO NOT GIVE USERS ACCESS TO THESE METHODS. THEY ARE NOT SECURE OR EVEN REALLY STABLE.
    def __render_content(self):
        rendered_content = self.__render_section_links(str(self.content))
        rendered_content = self.__render_columns(rendered_content)
        rendered_content = self.__render_gm_tip(rendered_content)
        rendered_content = self.__render_examples(rendered_content)
        rendered_content = self.__render_images(rendered_content)
        return rendered_content

    def to_url(self):
        guidebook_url = self.book.get_url()
        return "{}#{}".format(guidebook_url, self.slug)

    def __render_images(self, content):
        return re.sub(r"(<p>[\s]*)?\{![\s]*image(-sm)? ([\w./-]+)[\s]*!\}([\s]*</p>)?",
                      lambda x: '<div class="css-guide-image{}" style="background-image: url(\'{}\');"></div>'.format(
                          x.group(2) if x.group(2) else "",
                          get_object_or_404(GuidePic, slug=x.group(3)).picture.url),
                      content)

    # {{article-slug|link-text}} to link to that article
    def __render_section_links(self, content):
        return re.sub(r"\{\{([\w-]+)\|([\w\s-]+)\}\}", r"<a href=#\1>\2</a>", content)

    # {!col1!} {!col2!} {!colend!}
    def __render_columns(self, content):
        col1_start = '<div class="row"><div class="col-md-6 col-xs-12">'
        col2_start = '</div><div class="col-md-6 col-xs-12">'
        col_end = '</div></div>'
        rendered_content = re.sub(r"(<p>[\s]*)?\{!col1!\}([\s]*</p>)?", col1_start, content)
        rendered_content = re.sub(r"(<p>[\s]*)?\{!col2!\}([\s]*</p>)?", col2_start, rendered_content)
        rendered_content = re.sub(r"(<p>[\s]*)?\{!colend!\}([\s]*</p>)?", col_end, rendered_content)
        return rendered_content

    def __render_gm_tip(self, content):
        start = '<div class="css-gm-tip"><div class="css-gm-tip-header"><div class="css-guide-image-xs" style="background-image: url(\'{}\')"></div> GM Tip</div><div class="css-gm-tip-content">'\
            .format(static("guide/graphics/Sky_D10.png"))
        end = '</div></div>'
        rendered_content = re.sub(r"(<p>[\s]*)?\{!start-gm-tip!\}([\s]*</p>)?", start, content)
        rendered_content = re.sub(r"(<p>[\s]*)?\{!end-gm-tip!\}([\s]*</p>)?", end, rendered_content)
        return rendered_content

    def __render_examples(self, content):
        start = '<div class="css-examples">' \
                '<a class="wiki-entry-collapsible" role="button">' \
                '<div class="css-examples-header"><div class="css-guide-image-xs" style="background-image: url(\'{}\')">' \
                '</div> {} <small style="font-size: 12px; font-weight: 400;">(<span class="visible-xs-inline visible-sm-inline">tap</span><span class="hidden-xs hidden-sm">click</span> to expand)</small></div>' \
                '</a>' \
                '<div class="css-examples-content collapse-content"  style="display:none;">' \
            .format(static("guide/graphics/Pink_D10.png"), r"\2")
        end = '</div></div>'
        rendered_content = re.sub(r"(<p>[\s]*)?\{!start-examples\|([\w\s]+)!\}([\s]*</p>)?", start, content)
        rendered_content = re.sub(r"(<p>[\s]*)?\{!end-examples!\}([\s]*</p>)?", end, rendered_content)
        return rendered_content




    #Render text on save. Replaces
    # {{fancy-section}} with entire section

class GuidePic(models.Model):
    slug = models.SlugField(primary_key=True)
    picture = models.ImageField()
