from django.shortcuts import render
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect

from django.db import transaction

from .models import GuideBook, GuideSection
from .forms import make_guide_section_form, DeleteGuideSectionForm

class ReadGuideBook(View):
    template_name = 'guide/read_guide.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __get_context_data(self):
        guidebook = get_object_or_404(GuideBook, pk=self.kwargs['guidebook_slug'])
        sections = GuideSection.objects.filter(book=guidebook, is_deleted=False).order_by('position').all()
        can_edit = self.request.user.is_superuser
        nav_list = '<ol class="nav nav-pills nav-stacked">'
        prev_section = None
        depth = 1
        num_sections = sections.count()
        for i, section in enumerate(sections):
            entry = ""
            if prev_section and prev_section.header_level < section.header_level:
                for x in range(section.header_level - prev_section.header_level):
                    entry = entry + '<ol class="nav nav-pills nav-stacked css-inner-nav-list">'
                    depth = depth + 1
            if prev_section and prev_section.header_level > section.header_level:
                for x in range(prev_section.header_level - section.header_level):
                    entry = entry + "</ol>"
                    depth = depth - 1
            entry = entry + '<li role="presentation" class="{}"><a href="#{}">{}</a></li>'.format(
                'js-last-section' if i == num_sections - 1 else "js-first-section" if i == 0 else "",
                section.slug,
                section.title)
            nav_list = nav_list + entry
            prev_section = section
        for x in range(depth):
            nav_list = nav_list + "</ol>"
        context = {
            "guidebook": guidebook,
            "sections": sections,
            "can_edit": can_edit,
            "nav_list": nav_list,
        }
        return context

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class DeleteGuideSection(View):
    template_name = 'guide/delete_guide_section.html'
    guidebook = None
    current_section = None # currently editing section

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Only admins can edit the players guide")
        self.guidebook = get_object_or_404(GuideBook, pk=self.kwargs['guidebook_slug'])
        self.current_section = get_object_or_404(GuideSection, book=self.kwargs['guidebook_slug'],
                                                 slug=self.kwargs['section_slug'])
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = DeleteGuideSectionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                self.current_section.is_deleted = True
                self.current_section.save()
        return HttpResponseRedirect(reverse('guide:read_guidebook', args=(self.guidebook.slug,)))

    def __get_context_data(self):
        context = {
            'form': DeleteGuideSectionForm(self.request.POST),
            'guidebook': self.guidebook,
            'current_section': self.current_section,
        }
        return context

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class WriteGuideSection(View):
    template_name = 'guide/edit_guide.html'
    initial = None
    section = None
    guidebook = None
    previous_section = None # Section before this one
    current_section = None # currently editing section
    next_section = None  # Section after this one

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied("Only admins can edit the players guide")
        self.guidebook = get_object_or_404(GuideBook, pk=self.kwargs['guidebook_slug'])
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __get_context_data(self):
        context = {
            'form': make_guide_section_form(previous_section=self.previous_section,
                                            next_section=self.next_section)(initial=self.initial),
            'guidebook': self.guidebook,
            'previous_section': self.previous_section,
            'current_section': self.current_section,
            'next_section': self.next_section,
        }
        return context

class WriteNewGuideSection(WriteGuideSection):
    initial = {
    }

    def dispatch(self, *args, **kwargs):
        if 'section_slug' in self.kwargs:
            # write new section after provided section
            self.previous_section = get_object_or_404(GuideSection, book=self.kwargs['guidebook_slug'], slug=self.kwargs['section_slug'])
            guidebook = get_object_or_404(GuideBook, pk=self.kwargs['guidebook_slug'])
            sections = GuideSection.objects.filter(book=guidebook, is_deleted=False).order_by('position').all()
            num_sections = GuideSection.objects.filter(book=guidebook, is_deleted=False).order_by('position').count()
            for i, section in enumerate(sections):
                if section.id == self.previous_section.id:
                    if i+1 < num_sections:
                        self.next_section = sections[i+1]
            if self.next_section and self.previous_section:
                initial_pos = (self.next_section.position + self.previous_section.position) // 2
            else:
                initial_pos = self.previous_section.position + 10000
            initial_header_level = self.previous_section.header_level
        else:
            # no previous section in guidebook
            initial_pos = 1
            initial_header_level = 1
        self.initial = {
            "position": initial_pos,
            "header_level": initial_header_level,
        }
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = make_guide_section_form(previous_section=self.previous_section,
                                       next_section=self.next_section)(request.POST, initial=self.initial)
        if form.is_valid():
            with transaction.atomic():
                new_section = GuideSection(
                    book=self.guidebook,
                    title=form.cleaned_data['title'],
                    header_level=form.cleaned_data['header_level'],
                    slug=form.cleaned_data['slug'],
                    position=form.cleaned_data['position'],
                    content=form.cleaned_data['content'],
                    rendered_content=form.cleaned_data['content'], # initially just unrendered content
                    last_editor=request.user,
                    edit_date=timezone.now(),
                )
                new_section.save()
            return HttpResponseRedirect("{}#{}".format(
                reverse('guide:read_guidebook', args=(self.guidebook.slug,)),
                new_section.slug))
        raise ValueError("Invalid section form")


class EditGuideSection(WriteGuideSection):
    def dispatch(self, *args, **kwargs):
        self.current_section = get_object_or_404(GuideSection, book=self.kwargs['guidebook_slug'], slug=self.kwargs['section_slug'])
        previous_sections = GuideSection.objects\
            .filter(book=self.kwargs['guidebook_slug'], position__lt=self.current_section.position)\
            .order_by('position')
        if previous_sections.count() > 0:
            self.previous_section = previous_sections.all().last()
        next_sections = GuideSection.objects \
            .filter(book=self.kwargs['guidebook_slug'], position__gt=self.current_section.position) \
            .order_by('position')
        if next_sections.count() > 0:
            self.next_section = next_sections.all().last()
        self.initial = {
            "title": self.current_section.title,
            "content": self.current_section.content,
            "slug": self.current_section.slug,
            "position": self.current_section.position,
            "header_level": self.current_section.header_level,
        }
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = make_guide_section_form(previous_section=self.previous_section,
                                       next_section=self.next_section)(request.POST, initial=self.initial)
        if form.is_valid():
            with transaction.atomic():
                self.section = GuideSection.objects.select_for_update().get(pk=self.current_section.pk)
                self.section.title = form.cleaned_data["title"]
                self.section.position = form.cleaned_data["position"]
                self.section.header_level = form.cleaned_data["header_level"]
                self.section.slug = form.cleaned_data["slug"]
                self.section.content = form.cleaned_data['content']
                self.section.last_editor = request.user
                self.section.edit_date = timezone.now()
                self.section.save()
            return HttpResponseRedirect("{}#{}".format(
                reverse('guide:read_guidebook', args=(self.guidebook.slug,)),
                self.section.slug))
        raise ValueError("Invalid section form")
