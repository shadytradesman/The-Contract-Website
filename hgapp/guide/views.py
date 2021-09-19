from django.shortcuts import render
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import GuideBook, GuideSection

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
    template_name = 'guide/write_guide.html'
    initial = None
    guide_section = None

    def dispatch(self, *args, **kwargs):
        self.game = get_object_or_404(Game, id=self.kwargs['game_id'])
        self.character = get_object_or_404(Character, id=self.kwargs['character_id'])
        self.game_attendance = get_object_or_404(Game_Attendance, attending_character=self.character, relevant_game=self.game)
        redirect = self.__check_permissions()
        if redirect:
            return redirect
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            with transaction.atomic():
                journal = Journal(title=form.cleaned_data['title'],
                                  writer=request.user,
                                  game_attendance=self.game_attendance,
                                  is_downtime=self.is_downtime,
                                  is_deleted=False,
                                  is_nsfw=form.cleaned_data['is_nsfw'],
                                  contains_spoilers=form.cleaned_data['contains_spoilers'])
                journal.save()
                journal.set_content(form.cleaned_data['content'])
            return HttpResponseRedirect(reverse('journals:journal_read_game', args=(self.character.id, self.game.id)))
        raise ValueError("Invalid journal form")

    def __check_permissions(self):
        if not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You cannot edit this Contractor's Journal")
        if not (self.game.is_recorded() or self.game.is_finished() or self.game.is_archived()):
            return HttpResponseRedirect(reverse('journals:journal_read', args=(self.character.id, self.game.id)))

    def __get_context_data(self):
        context = {
            'game': self.game,
            'character': self.character,
            'attendance': self.game_attendance,
            'form': self.form_class(initial=self.initial),
            'is_downtime': self.is_downtime,
            'journal': self.journal,
        }
        return context
