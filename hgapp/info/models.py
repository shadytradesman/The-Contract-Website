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
    is_contested = models.BooleanField(default=False)
    is_secondary = models.BooleanField(default=False)
    is_first_roll = models.BooleanField(default=False)
    additional_rules_info = models.TextField(max_length=3000, default="")
    outcome_botch = models.TextField(max_length=3000)
    outcome_botch_extra = models.TextField(max_length=3000, blank=True, null=True)
    outcome_failure = models.TextField(max_length=3000)
    outcome_failure_extra = models.TextField(max_length=3000, blank=True, null=True)
    outcome_partial_success = models.TextField(max_length=3000)
    outcome_partial_success_extra = models.TextField(max_length=3000, blank=True, null=True)
    outcome_complete_success = models.TextField(max_length=3000)
    outcome_complete_success_extra = models.TextField(max_length=3000, blank=True, null=True)
    outcome_exceptional_success = models.TextField(max_length=3000)
    outcome_exceptional_success_extra = models.TextField(max_length=3000, blank=True, null=True)

    def json_serialize(self):
        json_object = {}
        json_object["actionText"] = self.action
        json_object["outcomeBotch"] = self.outcome_botch
        json_object["outcomeBotchExtra"] = self.outcome_botch_extra
        json_object["outcomeFailure"] = self.outcome_failure
        json_object["outcomeFailureExtra"] = self.outcome_failure_extra
        json_object["outcomePartialSuccess"] = self.outcome_partial_success
        json_object["outcomePartialSuccessExtra"] = self.outcome_partial_success_extra
        json_object["outcomeCompleteSuccess"] = self.outcome_complete_success
        json_object["outcomeCompleteSuccessExtra"] = self.outcome_complete_success_extra
        json_object["outcomeExceptionalSuccess"] = self.outcome_exceptional_success
        json_object["outcomeExceptionalSuccessExtra"] = self.outcome_exceptional_success_extra
        json_object["additionalRules"] = self.additional_rules_info
        json_object["isContested"] = self.is_contested
        json_object["isSecondary"] = self.is_secondary
        json_object["firstAction"] = self.is_first_roll
        roll_json = {}
        roll_json["attributeId"] = self.roll.attribute.id
        roll_json["attributeName"] = self.roll.attribute.name
        roll_json["abilityId"] = self.roll.ability.id
        roll_json["abilityName"] = self.roll.ability.name
        roll_json["difficulty"] = self.roll.difficulty
        json_object["roll"] = roll_json
        return json_object
