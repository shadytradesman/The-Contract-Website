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
    outcome_failure = models.CharField(max_length=3000)
    outcome_partial_success = models.CharField(max_length=3000)
    outcome_complete_success = models.CharField(max_length=3000)
    outcome_exceptional_success = models.CharField(max_length=3000)

    def json_serialize(self):
        json_object = {}
        json_object["actionText"] = self.action
        json_object["outcomeBotch"] = self.outcome_botch
        json_object["outcomeFailure"] = self.outcome_failure
        json_object["outcomePartialSuccess"] = self.outcome_partial_success
        json_object["outcomeCompleteSuccess"] = self.outcome_complete_success
        json_object["outcomeExceptionalSuccess"] = self.outcome_exceptional_success
        roll_json = {}
        roll_json["attributeId"] = self.roll.attribute.id
        roll_json["attributeName"] = self.roll.attribute.name
        roll_json["abilityId"] = self.roll.ability.id
        roll_json["abilityName"] = self.roll.ability.name
        roll_json["difficulty"] = self.roll.difficulty
        json_object["roll"] = roll_json
        return json_object
