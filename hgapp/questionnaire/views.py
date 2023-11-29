from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseRedirect

from characters.models import Character, EXP_QUESTIONNAIRE_PRE_CONTRACT, EXP_QUESTIONNAIRE_CONTRACT, EXP_REWARD_VALUES

from .models import Question, Answer

from .forms import AnswerForm


@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    character = answer.relevant_character
    if character.player != request.user:
        raise PermissionDenied("Only a Contractor's creator can answer their questionnaire")
    if answer.written_contract_number != character.number_completed_games():
        raise PermissionDenied("You cannot edit questionnaire answers for previous Contracts")
    if request.method == 'POST':
        with transaction.atomic():
            answer = Answer.objects.select_for_update().filter(id=answer_id).first()
            form = AnswerForm(request.POST)
            if form.is_valid():
                if request.user.profile.view_adult_content:
                    answer.is_nsfw = form.cleaned_data['is_nsfw']
                answer.set_content(form.cleaned_data['content'])
            else:
                raise ValueError("Invalid edit answer form")
            return HttpResponseRedirect(reverse('questionnaire:questionnaire_view', args=(character.id,)))
    else:
        initial = {
            'content': answer.content,
            'is_nsfw': answer.is_nsfw,
        }
        form = AnswerForm(initial)
        context = {
            "existing_answer": answer,
            "question": answer.question,
            "form": form,
            "character": character,
        }
        return render(request, 'questionnaire/answer.html', context)


@login_required
def answer_next(request, character_id, question_id=None):
    character = get_object_or_404(Character, id=character_id)
    if character.player != request.user:
        raise PermissionDenied("Only a Contractor's creator can answer their questionnaire")
    if request.method == 'POST':
        if question_id is None:
            raise ValueError("Must provide question_id in url when answering questions")
        with transaction.atomic():
            next_question = Question.next_question_for_character(character)
            if next_question is None or next_question.id != question_id:
                raise ValueError("Next question's ID does not match submitted question ID. Please try again.")
            form = AnswerForm(request.POST)
            if form.is_valid():
                existing_answer = Answer.objects.filter(relevant_character=character, question=next_question,
                                                        is_valid=False).first()
                if existing_answer is None:
                    answer = Answer(
                        question=next_question,
                        relevant_character=character,
                        writer=request.user,
                        game_attendance=character.get_latest_attendance(),
                        written_contract_number=character.number_completed_games(),
                        is_nsfw=form.cleaned_data['is_nsfw'],
                    )
                    answer.save()
                    answer.set_content(form.cleaned_data['content'])
                else:
                    existing_answer.set_content(form.cleaned_data['content'])
            else:
                raise ValueError("Invalid question form")
            subsequent_question = Question.next_question_for_character(character)
            if subsequent_question is not None and subsequent_question != next_question:
                return HttpResponseRedirect(reverse('questionnaire:questionnaire_answer', args=(character_id,)))
            else:
                # no additional questions to answer at this time.
                return HttpResponseRedirect(reverse('questionnaire:questionnaire_view', args=(character_id,)))
    else:
        next_question = Question.next_question_for_character(character)
        if next_question is None:
            return HttpResponseRedirect(reverse('questionnaire:questionnaire_view', args=(character_id,)))

        existing_answer = Answer.objects.filter(relevant_character=character, question=next_question,
                                                is_valid=False).first()
        if existing_answer is None:
            form = AnswerForm()
        else:
            initial = {
                'content': existing_answer.content,
                'is_nsfw': existing_answer.is_nsfw,
            }
            form = AnswerForm(initial)

        next_reward_type = "Exp"
        next_reward_quantity = 2
        questions_until_reward = 0
        num_answered_questions = Answer.objects.filter(is_valid=True, relevant_character=character).count()
        if num_answered_questions < 4:
            next_reward_quantity = EXP_REWARD_VALUES[EXP_QUESTIONNAIRE_PRE_CONTRACT]
            questions_until_reward = 0
        elif num_answered_questions == 4:
            next_reward_quantity = EXP_REWARD_VALUES[EXP_QUESTIONNAIRE_CONTRACT]
            questions_until_reward = 0
        elif num_answered_questions >= 5:
            if num_answered_questions % 2 != 0:
                questions_until_reward = 1
            if (num_answered_questions - 5) % 10 < 2:
                next_reward_type = "Improvement"
                next_reward_quantity = 1
        next_reward_string = "{} {}".format(next_reward_quantity, next_reward_type)
        context = {
            "question": next_question,
            "form": form,
            "character": character,
            "next_reward_string": next_reward_string,
            "questions_until_reward": questions_until_reward,
        }
        return render(request, 'questionnaire/answer.html', context)


def view_questionnaire(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_view(request.user):
        raise PermissionDenied("You cannot view the questionnaire of a contractor you can't view")
    context = {
        "character": character,
        "answers": Answer.objects.filter(relevant_character=character).order_by("written_contract_number", "id"),
        "can_edit": request.user == character.player,
        "next_question": Question.next_question_for_character(character),
    }
    return render(request, 'questionnaire/view.html', context)