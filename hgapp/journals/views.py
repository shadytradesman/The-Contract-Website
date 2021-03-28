import roman

from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.utils.decorators import classonlymethod

from .forms import JournalForm
from .models import Journal

from games.models import Game
from characters.models import Character

@method_decorator(login_required(login_url='account_login'), name='dispatch')
class WriteJournal(View):
    form_class = JournalForm
    template_name = 'journals/journal_form.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=()))

        return render(request, self.template_name, {'form': form})

    def __get_context_data(self):
        context = {
            'game': get_object_or_404(Game, id=self.kwargs['game_id']),
            'character': get_object_or_404(Character, id=self.kwargs['character_id']),
            'form': self.form_class(),
            'is_downtime': self.is_downtime,
        }
        return context

class WriteGameJournal(WriteJournal):
    is_downtime = False

class WriteDowntimeJournal(WriteJournal):
    is_downtime = True

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
            journal_page = {
                "header": roman.toRoman(i),
                "game": attendance.relevant_game,
                "id": "journal_page_{}".format(attendance.relevant_game.id),
            }
            journals = attendance.journal_set.filter(is_deleted=False)
            if journals.count() == 0:
                if viewer_can_write:
                    journal_page["journals"] = []
                    journal_pages.append(journal_page)
            else:
                journal_page["journals"] = journals.order_by("is_downtime", "created_date").all()
                journal_pages.append(journal_page)

        context = {
            'view_game_id': self.kwargs['game_id'] if 'game_id' in self.kwargs else None,
            'character': character,
            'viewer_can_write': viewer_can_write,
            'journal_pages': journal_pages,
        }
        return context

