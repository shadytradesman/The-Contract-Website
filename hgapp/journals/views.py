from django.shortcuts import render

from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from .models import Journal
from django.shortcuts import get_object_or_404

from games.models import Game
from characters.models import Character

class JournalCreate(CreateView):
    model = Journal
    fields = ['title', 'content', 'is_downtime']

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['game'] = get_object_or_404(Game, self.kwargs['game_id'])
        context['character'] = get_object_or_404(Character, self.kwargs['character_id'])
        return context
    # def get_object(self):
    #     this = self.get_form_kwargs()
    #     print(this)
    #     return

class JournalUpdate(UpdateView):
    model = Journal
    fields = ['name']