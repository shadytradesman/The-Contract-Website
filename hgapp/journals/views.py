from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse

from .forms import JournalForm
from .models import Journal

from games.models import Game
from characters.models import Character

@method_decorator(login_required(login_url=reverse('accounts:login')), name='dispatch')
class WriteJournal(View):
    form_class = JournalForm
    template_name = 'journals/journal_form.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(reverse('games:games_view_scenario', args=(scenario.id,)))

        return render(request, self.template_name, {'form': form})

    def __get_context_data(self):
        context = {
            'game': get_object_or_404(Game, self.kwargs['game_id']),
            'character': get_object_or_404(Character, self.kwargs['character_id']),
            'form': self.form_class(),
        }
        return context

class JournalUpdate(UpdateView):
    model = Journal
    fields = ['name']