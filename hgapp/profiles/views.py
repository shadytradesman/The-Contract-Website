from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.db import transaction


from profiles.forms import EditProfileForm
from profiles.models import Profile

class ProfileView(generic.DetailView):
    template_name = 'profiles/view_profile.html'

    def get_queryset(self):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        if self.profile.user == self.request.user:
            self.powers = self.profile.user.power_full_set.filter(is_deleted=False).order_by('-pub_date').all()
            self.characters = self.profile.user.character_set.filter(is_deleted=False).order_by('-edit_date').all()
        else:
            self.powers = self.profile.user.power_full_set.filter(private=False, is_deleted=False).order_by('-pub_date').all()
            self.characters = self.profile.user.character_set.filter(private=False).order_by('-edit_date').all()
        return Profile.objects

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['profile'] = self.profile
        context['powers'] = self.powers
        context['characters'] = self.characters
        return context

def my_profile_view(request):
    profile = get_object_or_404(Profile, pk=request.user.pk)
    powers = request.user.power_full_set.filter(is_deleted=False).order_by('-pub_date').all()
    characters = request.user.character_set.filter(is_deleted=False).order_by('-edit_date').all()
    context = {
        'profile': profile,
        'powers': powers,
        'characters': characters,
    }
    return render(request, 'profiles/view_profile.html', context)

def profile_edit(request):
    # TODO: replace this get object call with a more informative error page
    profile = get_object_or_404(Profile, pk=request.user.pk)
    if request.method == 'POST':
        form = EditProfileForm(request.POST)
        if form.is_valid():
            profile.about = form.cleaned_data['about']
            with transaction.atomic():
                profile.save()
            return HttpResponseRedirect(reverse('profiles:profiles_view_profile', args=(profile.id,)))
        else:
            print(form.errors)
            return None
    else:
        # Build a power form.
        form = EditProfileForm(
            initial={
                'about': profile.about,
            }
        )
        context = {
            'profile' : profile,
            'form' : form,
        }
        return render(request, 'profiles/edit_profile.html', context)