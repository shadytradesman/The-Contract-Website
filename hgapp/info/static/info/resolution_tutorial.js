const exampleActions = JSON.parse(document.getElementById('exampleActions').textContent);
const firstAction = JSON.parse(document.getElementById('firstAction').textContent);

var currentAction = 0;

function displayAction(rollElement, action) {
    const roller = $(rollElement);
    const actionNum = currentAction;
    if (actionNum === 0) {
        roller.find(".js-qs-prev-action").prop('disabled', true);
    } else {
        roller.find(".js-qs-prev-action").prop('disabled', false);
    }
    if (actionNum === exampleActions.length - 1) {
        roller.find(".js-qs-next-action").prop('disabled', true);
    } else {
        roller.find(".js-qs-next-action").prop('disabled', false);
    }
    roller.find(".js-qs-action-text").html(action.actionText);
    roller.find(".js-qs-attribute").html(action.roll.attributeName);
    roller.find(".js-qs-ability").html(action.roll.abilityName);
    roller.find(".js-roll-num-dice").attr("data-attr-id", action.roll.attributeId);
    roller.find(".js-roll-num-dice").attr("data-ability-id", action.roll.abilityId);
    var abilityValue = abilityValueById[action.roll.abilityId] != null ? abilityValueById[action.roll.abilityId] : 0;
    var attrValue = attributeValueById[action.roll.attributeId];
    roller.find(".js-qs-attribute-val").html(attrValue);
    console.log(abilityValue);
    roller.find(".js-qs-ability-val").html(abilityValue);
    roller.find(".js-qs-difficulty").html(action.roll.difficulty);
    updateRollValues();
    rollDice(roller, action);
}

function getRandomInt(max) {
    return Math.ceil(Math.random() * max);
}

function rollDice(roller, action) {
    const numDice = parseInt(roller.find(".js-qs-num-dice").html());
    var results = [];
    for (let i = 0; i < numDice; i++) {
        results[i] = getRandomInt(10);
    }
    results.sort(function(a, b) {
        return b - a;
    });
    roller.find(".js-qs-roll-results").html("");
    roller.find(".js-qs-roll-dice").html("");
    var diff = action.roll.difficulty;
    if (action.isSecondary) {
        roller.find(".js-qs-difficulty-extra")
            .html("(-1 Difficulty from using a Secondary Ability)");
    } else {
        roller.find(".js-qs-difficulty-extra").html("");
    }
    var outcome = 0;
    for (let i = 0; i < numDice; i++) {
        var successes = 0;
        if (results[i] === 10) {
            successes = 2;
        } else if (results[i] >= diff) {
            successes = 1;
        } else if (results[i] === 1) {
            successes = -1;
        }
        outcome = outcome + successes;
        if (successes > -1) {
            successes = "+" + successes;
        }
        roller.find(".js-qs-roll-results").append("<div class=\"css-quickstart-die-outcome\">" + successes + "</div>" );
        var dieFace = results[i];
        if (results[i] === 10) {
            dieFace = 0;
        }
        roller.find(".js-qs-roll-dice").append("<div class=\"css-quickstart-die\" style=\"background-image: url("
            + dieImageUrl + ")\"> <span class=\"css-quickstart-die-val\">" + dieFace + "</span></div>");
    }
    var outcomeText;
    if (action.isContested) {
        const combinedOutcome = outcome - 3;
        roller.find(".js-qs-contested-outcome").html(" - 3 (defender's Outcome) = " + combinedOutcome);
        if (combinedOutcome > 0) {
            outcomeText = "A positive contested Outcome means that the attempted action is successful.";
            roller.find(".js-qs-action-outcome").html(action.outcomeCompleteSuccess);
        } else if (combinedOutcome == 0) {
            outcomeText = "A contested Outcome of zero means that the attempted action fails. Ties go to the defender.";
            roller.find(".js-qs-action-outcome").html(action.outcomeFailure);
        } else if (combinedOutcome < 0) {
            outcomeText = "A negative contested Outcome means that the attempted action fails.";
            roller.find(".js-qs-action-outcome").html(action.outcomeFailure);
        }
    } else {
        roller.find(".js-qs-contested-outcome").html("");
        if (outcome > 5) {
            outcomeText = "An Outcome of 6 or more indicates an exceptional success with an additional positive effect.";
            roller.find(".js-qs-action-outcome").html(action.outcomeExceptionalSuccess);
        } else if (outcome > 3) {
            outcomeText = "An Outcome of 4 or 5 indicates a complete success.";
            roller.find(".js-qs-action-outcome").html(action.outcomeCompleteSuccess);
        } else if (outcome > 0) {
            outcomeText = "An Outcome of 1, 2, or 3 indicates a partial success or a success with a complication";
            roller.find(".js-qs-action-outcome").html(action.outcomePartialSuccess);
        } else if (outcome === 0) {
            outcomeText = "An Outcome of 0 is a failure.";
            roller.find(".js-qs-action-outcome").html(action.outcomeFailure);
        } else if (outcome < 0) {
            outcome = outcome + " (Botch)"
            outcomeText = "An Outcome of less than 0 is called a Botch and indicates that something went horribly wrong.";
            roller.find(".js-qs-action-outcome").html(action.outcomeBotch);
        }
    }
    roller.find(".js-qs-outcome-num").html(outcome);
    roller.find(".js-qs-outcome-explanation").html(outcomeText);
    if (action.additionalRules){
        roller.find(".js-additional-rules").html(action.additionalRules);
        roller.find(".js-additional-rules").show();
    } else {
        roller.find(".js-additional-rules").hide();
    }
}

$("#js-qs-roll-button").click(function () {
    var parent = $($(this).closest(".js-resolution-container")[0]);
    const action = exampleActions[currentAction];
    rollDice(parent,action);
})

$("#js-qs-roll-first-button").click(function () {
    var parent = $($(this).closest(".js-resolution-container")[0]);
    rollDice(parent,firstAction);
})

$(".js-qs-next-action").click(function () {
    var parent = $(this).closest(".js-resolution-container")[0];
    currentAction++;
    const action = exampleActions[currentAction];
    displayAction(parent, action);
})

$(".js-qs-prev-action").click(function () {
    var parent = $(this).closest(".js-resolution-container")[0];
    currentAction--;
    const action = exampleActions[currentAction];
    displayAction(parent, action);
})

window.onload = function () {
    const action = exampleActions[currentAction];
    displayAction($("#js-other-resolution"), action);
    displayAction($("#js-first-resolution"), firstAction);
}




