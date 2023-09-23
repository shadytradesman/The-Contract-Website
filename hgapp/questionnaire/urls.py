from django.urls import path

from . import views

app_name = 'questionnaire'
urlpatterns = [
    # ex: .com/questionnaire/answer/290
    path('answer/<int:character_id>', views.answer_next, name='questionnaire_answer'),
    path('answer/<int:character_id>/q/<int:question_id>', views.answer_next, name='questionnaire_answer_question'),

    # ex: .com/questionnaire/edit/a/2901
    path('edit/a/<int:answer_id>', views.edit_answer, name='questionnaire_edit'),

    # ex: .com/questionnaire/c/290
    path('c/<int:character_id>', views.view_questionnaire, name='questionnaire_view'),
]
