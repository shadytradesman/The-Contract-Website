from django.shortcuts import render
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied

from django.db import transaction

from .models import GuideBook, GuideSection
from .forms import GuideSectionForm

class ReadGuideBook(View):
    template_name = 'guide/read_guide.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __get_context_data(self):
        guidebook = get_object_or_404(GuideBook, pk=self.kwargs['guidebook_slug'])
        sections = GuideSection.objects.filter(book=guidebook, is_deleted=False).order_by('position').all()
        can_edit = self.request.user.is_superuser
        context = {
            "guidebook": guidebook,
            "sections": sections,
            "can_edit": can_edit,
        }
        return context

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class WriteGuideSection(View):
    form_class = GuideSectionForm
    template_name = 'guide/edit_guide.html'
    initial = None
    guide_section = None

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied("You cannot edit this Contractor's Journal")
        self.guidebook = get_object_or_404(GuideBook, pk=self.kwargs['guidebook_slug'])
        self.section = get_object_or_404(GuideSection, book=self.kwargs['guidebook_slug'], slug=self.kwargs['section_slug'])
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        # if form.is_valid():
        #     with transaction.atomic():
        #         journal = Journal(title=form.cleaned_data['title'],
        #                           writer=request.user,
        #                           game_attendance=self.game_attendance,
        #                           is_downtime=self.is_downtime,
        #                           is_deleted=False,
        #                           is_nsfw=form.cleaned_data['is_nsfw'],
        #                           contains_spoilers=form.cleaned_data['contains_spoilers'])
        #         journal.save()
        #         journal.set_content(form.cleaned_data['content'])
        #     return HttpResponseRedirect(reverse('journals:journal_read_game', args=(self.character.id, self.game.id)))
        raise ValueError("Invalid journal form")

    def __get_context_data(self):
        context = {
            'form': self.form_class(initial=self.initial),
            'guidebook': self.guidebook,
            'section': self.section,
        }
        return context

class WriteNewGuideSection(WriteGuideSection):
    initial = {
    }

class EditGuideSection(WriteGuideSection):
    def dispatch(self, *args, **kwargs):
        self.initial = {
            "title": self.guide_section.title,
            "content": self.guide_section.content,
        }
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        # if form.is_valid():
        #     title = form.cleaned_data['title']
        #     content = form.cleaned_data['content']
        #     with transaction.atomic():
        #         self.journal = Journal.objects.select_for_update().get(pk=self.journal.pk)
        #         self.journal.title = title
        #         self.journal.edit_date = timezone.now()
        #         self.journal.writer = request.user
        #         self.journal.contains_spoilers = form.cleaned_data['contains_spoilers']
        #         self.journal.is_nsfw = form.cleaned_data['is_nsfw']
        #         self.journal.save()
        #         self.journal.set_content(content)
        #     return HttpResponseRedirect(reverse('journals:journal_read_game', args=(self.character.id, self.game.id)))
        # else:
        raise ValueError("Invalid journal form.")
