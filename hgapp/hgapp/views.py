from itertools import chain
import datetime

from account.models import Account
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.http import (
    HttpResponse, HttpResponseGone, HttpResponseNotAllowed,
    HttpResponsePermanentRedirect, HttpResponseRedirect,
)
import account.views
from django.core.exceptions import PermissionDenied
from account.models import EmailAddress


# Create your views here.
from django.urls import reverse

from characters.models import Character, CharacterTutorial
from powers.models import Power_Full, Enhancement, Drawback, Parameter, Base_Power, SYS_LEGACY_POWERS, SYS_PS2

from games.models import GAME_STATUS, Scenario, Game, Game_Attendance, WIN, LOSS, DEATH
from hgapp.forms import SignupForm, ResendEmailConfirmation
from blog.models import Post
from info.models import FrontPageInfo
from cells.models import WorldEvent
from profiles.forms import EmailSettingsForm
from profiles.models import Profile
from notifications.models import Notification
from games.games_constants import get_completed_game_excludes_query


class SignupView(account.views.SignupView):
   form_class = SignupForm

   def create_account(self, form):
       return Account.create(request=self.request, user=self.created_user, create_email=False, timezone=form.cleaned_data["timezone"])


class LoginView(account.views.LoginView):
    def get_initial(self):
        return {
            "remember": True
        }


class SettingsView(account.views.SettingsView):
    def get_context_data(self, **kwargs):
        ctx = super(SettingsView, self).get_context_data(**kwargs)
        if self.request.user.profile:
            profile = self.request.user.profile
            email_prefs_initial = {
                "contract_invitations": profile.contract_invitations,
                "contract_updates": profile.contract_updates,
                "intro_contracts": profile.intro_contracts,
                "direct_messages": profile.direct_messages,
                "site_announcements": profile.site_announcements,
            }
            ctx["email_settings_form"] = EmailSettingsForm(initial=email_prefs_initial)
        return ctx

    def update_settings(self, form, **kwargs):
        super(SettingsView, self).update_settings(form, **kwargs)
        email_form = EmailSettingsForm(self.request.POST)
        if email_form.is_valid() and self.request.user.profile:
            profile = self.request.user.profile
            profile.contract_invitations = email_form.cleaned_data["contract_invitations"]
            profile.intro_contracts = email_form.cleaned_data["intro_contracts"]
            profile.contract_updates = email_form.cleaned_data["contract_updates"]
            profile.direct_messages = email_form.cleaned_data["direct_messages"]
            profile.site_announcements = email_form.cleaned_data["site_announcements"]
            profile.save()


class PasswordResetTokenView(account.views.PasswordResetTokenView):
    def get_context_data(self, **kwargs):
        ctx = super(PasswordResetTokenView, self).get_context_data(**kwargs)
        ctx["user"] = self.get_user()
        return ctx


@method_decorator(login_required(login_url='account_login'), name='dispatch')
class ResendConfirmation(View):
    template_name = "account/resend_confirmation.html"
    form_class = ResendEmailConfirmation
    user = None
    email = None

    def dispatch(self, *args, **kwargs):
        self.user = self.request.user
        self.email = EmailAddress.objects.get_primary(self.user)
        if self.email is None:
            messages.add_message(self.request, messages.SUCCESS,
                                 "Please enter an email address before sending confirmation")
            return HttpResponseRedirect(reverse('account_settings'))
        if self.email.verified:
            messages.add_message(self.request, messages.SUCCESS, "Email successfully verified")
            return HttpResponseRedirect(reverse('account_settings'))
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            self.email.send_confirmation()
            messages.add_message(self.request, messages.INFO, "Resent Confirmation email to {}".format(self.email.email))
            return HttpResponseRedirect(reverse('account_settings'))
        raise ValueError("Invalid journal form")

    def __check_permissions(self):
        if not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You cannot edit this Contractor's Journal")
        if not (self.game.is_recorded() or self.game.is_finished() or self.game.is_archived()):
            return HttpResponseRedirect(reverse('journals:journal_read', args=(self.character.id, self.game.id)))

    def __get_context_data(self):
        context = {
            'form': self.form_class(),
            'email': self.email,
        }
        return context


def home(request):
    if request.user.is_anonymous:
        info = FrontPageInfo.objects.first()
        tutorial = CharacterTutorial.objects.first()
        num_players = Profile.objects.count()
        num_scenarios_with_valid_writeups = Scenario.objects.filter(num_words__gte=1000).count()
        num_contractors = Character.objects.count()
        num_victories = Game_Attendance.objects.filter(outcome=WIN, is_confirmed=True).count()
        num_losses = Game_Attendance.objects.filter(outcome=LOSS, is_confirmed=True).count()
        num_deaths = Game_Attendance.objects.filter(outcome=DEATH, is_confirmed=True).count()
        now = datetime.datetime.now()
        two_hours_ago = now - datetime.timedelta(hours=2)
        games = Game.objects.filter(
            list_in_lfg=True,
            status=GAME_STATUS[0][0],
            scheduled_start_time__gte=two_hours_ago)\
            .exclude(is_nsfw=True)\
            .select_related("scenario")\
            .order_by('scheduled_start_time')[:3]
        num_games = Game.objects.filter(
            list_in_lfg=True,
            status=GAME_STATUS[0][0],
            scheduled_start_time__gte=two_hours_ago).exclude(is_nsfw=True).count()
        context = {
            'info': info,
            'tutorial': tutorial,
            "num_players": num_players,
            "num_contractors": num_contractors,
            "num_scenarios_with_valid_writeups": num_scenarios_with_valid_writeups,
            "num_victories":  num_victories,
            "num_losses": num_losses,
            "num_deaths": num_deaths,
            "games": games,
            "num_games": num_games,
        }
        return render(request, 'logged_out_homepage.html', context)
    else:
        if hasattr(request.user, 'profile'):
            if not request.user.profile.confirmed_agreements:
                return HttpResponseRedirect(reverse('profiles:profiles_terms'))
        my_characters = request.user.character_set.filter(is_deleted=False).order_by('name').all()
        living_characters = [x for x in my_characters if x.is_dead == False]
        dead_characters = [x for x in my_characters if x.is_dead == True]
        my_powers = request.user.power_full_set.filter(is_deleted=False).order_by('name').all()
        my_scenarios = request.user.scenario_creator.order_by("title").all()
        new_players = User.objects.order_by('-date_joined').filter(profile__is_private=False)[:6]
        new_powers = Power_Full.objects.filter(private=False, is_deleted=False).filter(owner__profile__is_private=False).order_by('-id')[:6]
        new_characters = Character.objects.filter(private=False, is_deleted=False).filter(player__profile__is_private=False).order_by('-id')[:6]
        latest_blog_post = Post.objects.current().select_related("section", "blog").first()
        upcoming_games_running = request.user.game_creator.filter(status=GAME_STATUS[0][0]).all()
        upcoming_games_invited = request.user.game_invite_set.filter(relevant_game__status=GAME_STATUS[0][0], is_declined=False).all()
        active_games_attending = request.user.game_set.filter(status=GAME_STATUS[1][0])
        active_games_creator = request.user.game_creator.filter(status=GAME_STATUS[1][0])
        active_games = list(chain(active_games_attending, active_games_creator))
        avail_improvements = request.user.profile.get_avail_improvements()
        avail_charon_coins = request.user.profile.get_avail_charon_coins()
        avail_exp_rewards = request.user.profile.get_avail_exp_rewards()
        cells = request.user.cell_set.filter(cellmembership__is_banned=False).all()
        cell_ids = set(request.user.cell_set.values_list('id', flat=True).all())
        world_events = WorldEvent.objects.filter(parent_cell__id__in=cell_ids).order_by('-created_date').all()
        cell_invites = request.user.cellinvite_set.filter(membership=None).filter(is_declined=False).all()
        attendance_invites_to_confirm = request.user.game_invite_set.filter(attendance__is_confirmed=False).exclude(is_declined=True).all()
        email = EmailAddress.objects.get_primary(request.user)
        email_verified = email and email.verified

        timeline_notifications = Notification.get_timeline_notifications_for_player_queryset(request.user)
        context = {
            'living_characters': living_characters,
            'dead_characters': dead_characters,
            'powers': my_powers,
            'my_scenarios': my_scenarios,
            'new_players': new_players,
            'new_powers': new_powers,
            'new_characters': new_characters,
            'upcoming_games_running': upcoming_games_running,
            'upcoming_games_invited': upcoming_games_invited,
            'active_games': active_games,
            'avail_improvements': avail_improvements,
            'avail_charon_coins': avail_charon_coins,
            'cells': cells,
            'cell_invites': cell_invites,
            'world_events': world_events[:3],
            'attendance_invites_to_confirm': attendance_invites_to_confirm,
            'avail_exp_rewards': avail_exp_rewards,
            'latest_blog_post': latest_blog_post,
            'email_verified': email_verified,
            'timeline_notifications': timeline_notifications,
            'expand_contractors': True,
            'expand_playgroups': cells.count() < 5,
            'expand_gifts': my_powers.count() < 3,
            'expand_contracts': True,
        }
        if hasattr(request.user, 'profile'):
            if request.user.profile.early_access_user:
                return render(request, 'new_logged_in_homepage.html', context)
        return render(request, 'logged_in_homepage.html', context)

def csrf_failure(request, reason=""):
    raise PermissionDenied("CSRF token failure. Refresh form and try again.")


class RedirectRootUrlView(View):
    """Provide a redirect on any GET request."""
    permanent = False
    new_root = None

    def get_redirect_url(self, *args, **kwargs):
        path = self.request.get_full_path()
        second_slash_index = path[1:].find('/') + 1
        new_path = path[second_slash_index:]
        return self.new_root + new_path

    def get(self, request, *args, **kwargs):
        url = self.get_redirect_url(*args, **kwargs)
        if url:
            if self.permanent:
                return HttpResponsePermanentRedirect(url)
            else:
                return HttpResponseRedirect(url)
        else:
            return HttpResponseGone()

    def head(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
