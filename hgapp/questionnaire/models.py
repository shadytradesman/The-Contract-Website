from django.db import models
from django.conf import settings

from bs4 import BeautifulSoup

from django.urls import reverse

from games.models import Game_Attendance, Reward

from characters.models import Character, ExperienceReward, EXP_QUESTIONNAIRE_CONTRACT, EXP_QUESTIONNAIRE_INITIAL

from notifications.models import Notification, REWARD_NOTIF, JOURNAL_NOTIF


class Question(models.Model):
    prompt = models.CharField(max_length=400)
    min_word_count = models.IntegerField(default=150)
    is_repeatable = models.BooleanField(default=True)
    contract_number = models.IntegerField(default=0)

    def __str__(self):
        return "Contract {} - {}".format(self.contract_number, self.prompt)

    class Meta:
        indexes = [
            models.Index(fields=['contract_number']),
        ]

    @staticmethod
    def next_question_for_character(character):
        game_number = character.number_completed_games()
        num_answered_questions = Answer.objects.filter(relevant_character=character, is_valid=True).count()
        num_questions_available = Question.objects.exclude(contract_number__gt=game_number).count()
        if num_answered_questions < num_questions_available:
            next_questions = Question.objects\
                .exclude(contract_number__gt=game_number)\
                .order_by('contract_number', 'id')
            next_question_by_number = next_questions[num_answered_questions]
            previously_answered = Answer.objects.filter(relevant_character=character, question=next_question_by_number).first()
            if previously_answered is None or not previously_answered.is_valid:
                return next_question_by_number
            else:
                # find the first question without an answer. This can happen if an attendance is deleted.
                for question in next_questions:
                    previously_answered = Answer.objects.filter(relevant_character=character,
                                                                question=next_question_by_number).first()
                    if previously_answered is None:
                        return question
        num_unique_questions = Question.objects.count()
        if num_answered_questions >= num_unique_questions:
            # They've gone through all questions at least once. Got to check repeats.
            num_repeatable_questions = Question.objects.filter(is_repeatable=True).count()
            if num_answered_questions >= num_unique_questions + num_repeatable_questions:
                # Character has completely finished questionnaire including all repeats
                return None
            repeatable_answers = Answer.objects \
                .filter(relevant_character=character,
                        is_valid=True,
                        question__is_repeatable=True,
                        written_contract_number__lt=game_number - 9)\
                .order_by("written_contract_number", "id")
            if num_answered_questions < len(repeatable_answers) + num_unique_questions:
                # Valid repeatable questions remain to be answered
                return repeatable_answers[num_answered_questions - num_unique_questions].question
        return None


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    relevant_character = models.ForeignKey(Character, on_delete=models.CASCADE)
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT)
    game_attendance = models.ForeignKey(Game_Attendance, on_delete=models.CASCADE, null=True)
    written_contract_number = models.IntegerField(default=0)
    content = models.TextField(max_length=100000, null=True, blank=True)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    is_valid = models.BooleanField(default=False)
    is_nsfw = models.BooleanField(default=False)
    experience_reward = models.OneToOneField(ExperienceReward,
                                             null=True,
                                             blank=True,
                                             on_delete=models.SET_NULL)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_character']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['relevant_character', 'game_attendance', 'question'], name='unique_answer'),
            models.UniqueConstraint(fields=['relevant_character', 'written_contract_number', 'question'], name='unique_answer_2'),
        ]

    def __str__(self):
        return "{} answered {}".format(self.relevant_character.name, self.question.prompt)

    def get_url(self):
        return "{}#answer-{}".format(reverse('questionnaire:questionnaire_view', args=(self.relevant_character_id,)), self.pk)

    def set_content(self, content):
        original_valid = self.is_valid
        is_valid = self.__get_is_valid(content)
        if is_valid:
            # once valid, an answer cannot become invalid. This is SUPER IMPORTANT for tracking reward provenance
            self.is_valid = is_valid
        self.content = content
        self.save()
        if self.is_valid and not original_valid:
            self.grant_reward()
            self.send_notifications()

    def send_notifications(self):
        if not self.relevant_character.private:
            num_answered_questions = Answer.objects.filter(is_valid=True,
                                                           relevant_character=self.relevant_character).count()
            if num_answered_questions != 5 and (num_answered_questions - 5) % 6 != 0:
                return
            cell = self.relevant_character.cell if hasattr(self.relevant_character, "cell") else None
            if cell is not None:
                members = cell.get_unbanned_members()
                for player_membership in members:
                    player = player_membership.member_player
                    if player is not None:
                        Notification.objects.create(
                            user=player,
                            headline="{} is answering their Questionnaire".format(self.relevant_character.name),
                            content="{} has answered {} questions".format(self.relevant_character.name, num_answered_questions),
                            url=reverse('questionnaire:questionnaire_view', args=(self.relevant_character_id,)),
                            notif_type=JOURNAL_NOTIF)

    def __get_is_valid(self, content):
        word_count = self.__get_wordcount(content)
        # use slightly fewer words than what we tell people in case our counting sucks
        return word_count >= (self.question.min_word_count - 3)

    def __get_wordcount(self, content):
        soup = BeautifulSoup(content, features="html5lib")
        return len(soup.text.split())

    def get_improvement(self):
        if hasattr(self, "game_attendance") and self.game_attendance is not None:
            return Reward.objects.filter(rewarded_player=self.writer,
                                         relevant_game=self.game_attendance.relevant_game,
                                         is_void=False,
                                         is_questionnaire=True)\
                                 .order_by('-awarded_on')\
                                 .first()

    def get_exp_reward(self):
        if hasattr(self, "experience_reward") and self.experience_reward:
            return self.experience_reward
        else:
            return None

    def grant_reward(self):
        if not self.is_valid:
            return
        if hasattr(self, "game_attendance") and self.game_attendance and \
                hasattr(self.game_attendance, "attending_character") and self.game_attendance.attending_character:
            if self.game_attendance.attending_character != self.relevant_character:
                raise ValueError("attendance character does not match answer character")
        num_answered_questions = Answer.objects.filter(is_valid=True, relevant_character=self.relevant_character).count()
        if self.experience_reward and not self.experience_reward.is_void:
            raise ValueError("questionnaire is granting exp reward when it already has one.", str(self.id))
        if num_answered_questions == 5:
            exp_reward = ExperienceReward(
                rewarded_character=self.relevant_character,
                rewarded_player=self.writer,
                type=EXP_QUESTIONNAIRE_INITIAL,
            )
            exp_reward.save()
            self.experience_reward = exp_reward
            self.save()
            Notification.objects.create(
                user=self.writer,
                headline="Exp earned from Questionnaire",
                content="{} earned 5 Exp".format(self.relevant_character.name),
                url=reverse("characters:characters_spend_reward", args=[self.relevant_character.id]),
                notif_type=REWARD_NOTIF)
            return
        elif num_answered_questions >= 7 and num_answered_questions % 2 != 0:
            if ((num_answered_questions - 7) / 2) % 5 == 0:
                reward = Reward(relevant_game=self.game_attendance.relevant_game,
                                rewarded_character=self.relevant_character,
                                rewarded_player=self.writer,
                                is_improvement=True,
                                is_questionnaire=True)
                reward.save()
                Notification.objects.create(
                    user=self.writer,
                    headline="Improvement earned from Questionnaire",
                    content="{} earned an Improvement".format(self.relevant_character.name),
                    url=reverse("characters:characters_spend_reward", args=[self.relevant_character.id]),
                    notif_type=REWARD_NOTIF)
                return
            else:
                exp_reward = ExperienceReward(
                    rewarded_character=self.relevant_character,
                    rewarded_player=self.writer,
                    type=EXP_QUESTIONNAIRE_CONTRACT,
                )
                exp_reward.save()
                self.experience_reward = exp_reward
                self.save()
                Notification.objects.create(
                    user=self.writer,
                    headline="Exp earned from Questionnaire",
                    content="{} earned 2 Exp".format(self.relevant_character.name),
                    url=reverse("characters:characters_spend_reward", args=[self.relevant_character.id]),
                    notif_type=REWARD_NOTIF)
                return
