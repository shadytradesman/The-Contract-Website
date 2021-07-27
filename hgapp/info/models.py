from django.db import models

from characters.models import Character, Roll

class FrontPageInfo(models.Model):
    shown_fiction = models.TextField(max_length=30000)
    hidden_fiction = models.TextField(max_length=30000)

class QuickStartInfo(models.Model):
    main_char = models.ForeignKey(Character, on_delete=models.CASCADE)

class ExampleAction(models.Model):
    action = models.CharField(max_length=3000)
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)
    outcome_botch = models.CharField(max_length=3000)
    outcome_partial_success = models.CharField(max_length=3000)
    outcome_complete_success = models.CharField(max_length=3000)
    outcome_exceptional_success = models.CharField(max_length=3000)
