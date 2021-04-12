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
from django.db import transaction

from .forms import JournalForm, JournalCoverForm
from .models import Journal, JournalCover
from hgapp.utilities import get_object_or_none

from games.models import Game, Game_Attendance
from characters.models import Character
from characters.view_utilities import get_characters_next_journal_credit

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
                                  contains_spoilers=form.cleaned_data['contains_spoilers'])
                journal.save()
                journal.set_content(form.cleaned_data['content'])
            return HttpResponseRedirect(reverse('journals:journal_read', args=(self.character.id, self.game.id)))
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
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
            with transaction.atomic():
                if not title or not content:
                    self.journal.mark_void()
                else:
                    self.journal.title = title
                    self.journal.edit_date = timezone.now()
                    self.journal.writer = request.user
                    self.journal.contains_spoilers = form.cleaned_data['contains_spoilers']
                    self.journal.save()
                    self.journal.set_content(content)
            return HttpResponseRedirect(reverse('journals:journal_read', args=(self.character.id, self.game.id)))
        else:
            raise ValueError("Invalid journal form.")

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class EditCover(View):
    is_downtime = False # doesn't actually matter
    cover = None
    form_class = JournalCoverForm
    template_name = 'journals/cover_edit.html'
    initial = {}

    def dispatch(self, *args, **kwargs):
        self.character = get_object_or_404(Character, id=self.kwargs['character_id'])
        self.__check_permissions()
        self.cover = get_object_or_none(JournalCover, character=self.character)
        if self.cover:
            self.initial = {
                "title": self.cover.title,
                "content": self.cover.content,
            }
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            with transaction.atomic():
                title = form.cleaned_data['title']
                content = form.cleaned_data['content']
                if self.cover:
                    self.cover.title = title
                    self.cover.content = content
                    self.cover.save()
                else:
                    self.cover = JournalCover(character = self.character,
                                              title = title,
                                              content = content)
                    self.cover.save()
            return HttpResponseRedirect(reverse('journals:journal_read', args=(self.character.id,)))
        raise ValueError("Invalid journal cover form")

    def __check_permissions(self):
        if not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You cannot edit this Contractor's Journal")

    def __get_context_data(self):
        context = {
            'character': self.character,
            'form': self.form_class(initial=self.initial),
        }
        return context


class ReadJournal(View):
    template_name = 'journals/journal_read.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def __get_context_data(self):
        character = get_object_or_404(Character, id=self.kwargs['character_id'])
        viewer_can_write = character.player_can_edit(self.request.user)
        completed_attendances = character.completed_games()
        cover = get_object_or_none(JournalCover, character=character)
        journal_pages = []
        cover_id = "journal_page_cover"
        journal_page = {
            "header": "cover",
            "id": cover_id,
            "empty": False,
            "cover": cover if cover else {"title":"", "content": ""},
        }
        journal_pages.append(journal_page)
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
                game_journal = get_object_or_none(Journal,
                                   game_attendance=attendance,
                                   is_deleted=False,
                                   is_downtime=False)
                if game_journal:
                    game_journal.inject_viewable(self.request.user)
                journal_page["game_journal"] = game_journal
                journal_page["downtime_journals"] = journals.filter(is_downtime=True).order_by("created_date").all()
                for journal in journal_page["downtime_journals"]:
                    journal.inject_viewable(self.request.user)
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

        prev_page= None
        for journal_page in journal_pages:
            if prev_page:
                prev_page['next_id'] = journal_page['id']
                journal_page['prev_id'] = prev_page['id']
            prev_page = journal_page

        context = {
            'view_game_id': "journal_page_{}".format(self.kwargs['game_id']) if 'game_id' in self.kwargs else cover_id,
            'character': character,
            'viewer_can_write': viewer_can_write,
            'journal_pages': journal_pages,
        }
        return context


def write_next_journal(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_edit(request.user):
        raise PermissionDenied("You cannot edit this Contractor's Journal")
    next_journal_attendance = get_characters_next_journal_credit(character)
    if next_journal_attendance:
        attendance = next_journal_attendance["attendance"]
        if next_journal_attendance["is_downtime"]:
            return HttpResponseRedirect(reverse('journals:journal_write_downtime',
                                                args=(attendance.relevant_game.id, attendance.attending_character.id)))
        else:
            return HttpResponseRedirect(reverse('journals:journal_write_game',
                                                args=(attendance.relevant_game.id, attendance.attending_character.id)))
    else:
        return HttpResponseRedirect(reverse('journals:journal_read', args=(character.id,)))

