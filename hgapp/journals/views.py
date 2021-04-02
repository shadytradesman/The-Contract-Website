import roman

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from .forms import JournalForm
from .models import Journal
from hgapp.utilities import get_object_or_none

from games.models import Game, Game_Attendance
from characters.models import Character

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class WriteJournal(View):
    form_class = JournalForm
    template_name = 'journals/journal_write.html'
    initial = None
    journal = None

    def dispatch(self, *args, **kwargs):
        self.game = get_object_or_404(Game, id=self.kwargs['game_id'])
        self.character = get_object_or_404(Character, id=self.kwargs['character_id'])
        self.game_attendance = get_object_or_404(Game_Attendance, attending_character=self.character, relevant_game=self.game)
        self.__check_permissions()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            journal = Journal(title=form.cleaned_data['title'],
                              content=content,
                              writer=request.user,
                              game_attendance=self.game_attendance,
                              is_downtime=self.is_downtime,
                              is_deleted=False,
                              contains_spoilers=form.cleaned_data['contains_spoilers'])
            journal.save()
            return HttpResponseRedirect(reverse('journals:journal_read', args=(self.character.id, self.game.id)))
        raise ValueError("Invalid journal form")

    def __check_permissions(self):
       if not self.character.player_can_edit(self.request.user):
           raise PermissionDenied("You cannot edit this Contractor's Journal")

    def __get_context_data(self):
        context = {
            'game': self.game,
            'character': self.character,
            'form': self.form_class(initial=self.initial),
            'is_downtime': self.is_downtime,
            'journal': self.journal,
        }
        return context

class WriteGameJournal(WriteJournal):
    is_downtime = False

class WriteDowntimeJournal(WriteJournal):
    is_downtime = True

class EditJournal(WriteJournal):
    is_downtime = False # doesn't actually matter

    def dispatch(self, *args, **kwargs):
        self.journal = get_object_or_404(Journal, id=self.kwargs['journal_id'])
        self.initial = {
            "title": self.journal.title,
            "content": self.journal.content,
            "contains_spoilers": self.journal.contains_spoilers,
        }
        self.kwargs["game_id"] = self.journal.game_attendance.relevant_game.id
        self.kwargs["character_id"] = self.journal.game_attendance.attending_character.id
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            self.journal.content = content
            self.journal.title = form.cleaned_data['title']
            self.journal.edit_date = timezone.now()
            self.journal.writer = request.user
            self.journal.contains_spoilers = form.cleaned_data['contains_spoilers']
            self.journal.save()
            return HttpResponseRedirect(reverse('journals:journal_read', args=(self.character.id, self.game.id)))

        return render(request, self.template_name, {'form': form})

class ReadJournal(View):
    template_name = 'journals/journal_read.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __get_context_data(self):
        character = get_object_or_404(Character, id=self.kwargs['character_id'])
        viewer_can_write = character.player_can_edit(self.request.user)
        completed_attendances = character.completed_games()
        journal_pages = []
        for i, attendance in enumerate(completed_attendances, start=1):
            if attendance.is_death():
                continue
            journal_page = {
                "header": roman.toRoman(i),
                "game": attendance.relevant_game,
                "id": "journal_page_{}".format(attendance.relevant_game.id),
                "game_journal": None,
                "downtime_journals": [],
                "empty": False,
            }
            journals = attendance.journal_set.filter(is_deleted=False)
            if journals.count() == 0:
                if viewer_can_write:
                    journal_page["empty"] = True
                    journal_pages.append(journal_page)
            else:
                journal_page["game_journal"] = get_object_or_none(Journal,
                                                                  game_attendance=attendance,
                                                                  is_deleted=False,
                                                                  is_downtime=False)
                journal_page["downtime_journals"] = journals.filter(is_downtime=True).order_by("created_date").all()
                journal_pages.append(journal_page)
        death = character.real_death()
        if death:
            journal_page = {
                "header": "death",
                "game": death.game_attendance.relevant_game if hasattr(death, 'game_attendance') and death.game_attendance else None,
                "id": "journal_page_death",
                "game_journal": None,
                "downtime_journals": [],
                "empty": False,
                "death": death,
            }
            journal_pages.append(journal_page)

        context = {
            'view_game_id': self.kwargs['game_id'] if 'game_id' in self.kwargs else None,
            'character': character,
            'viewer_can_write': viewer_can_write,
            'journal_pages': journal_pages,
        }
        return context

