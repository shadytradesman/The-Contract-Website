const exampleActions = JSON.parse(document.getElementById('exampleActions').textContent);

var currentAction = 0;

function displayAction() {
    const actionNum = currentAction;
    if (actionNum === 0) {
        $("#js-qs-prev-action").prop('disabled', true);
    } else {
        $("#js-qs-prev-action").prop('disabled', false);
    }
    if (actionNum === exampleActions.length - 1) {
        $("#js-qs-next-action").prop('disabled', true);
    } else {
        $("#js-qs-next-action").prop('disabled', false);
    }
    const action = exampleActions[actionNum];
    $("#js-qs-action-text").html(action.actionText);
    $(".js-qs-attribute").html(action.roll.attributeName);
    $(".js-qs-ability").html(action.roll.abilityName);
    $(".js-roll-num-dice").attr("data-attr-id", action.roll.attributeId);
    $(".js-roll-num-dice").attr("data-ability-id", action.roll.abilityId);
    $("#js-qs-difficulty").html(action.roll.difficulty);
    updateRollValues();
    rollDice();
}

function getRandomInt(max) {
    return Math.ceil(Math.random() * max);
}

function rollDice() {
    const numDice = parseInt($("#js-qs-num-dice").html());
    var results = [];
    for (let i = 0; i < numDice; i++) {
        results[i] = getRandomInt(10);
    }
    results.sort(function(a, b) {
        return b - a;
    });
    $("#js-qs-roll-results").html("");
    $("#js-qs-roll-dice").html("");
    const action = exampleActions[currentAction];
    const diff = action.roll.difficulty;
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
        $("#js-qs-roll-results").append("<div class=\"css-quickstart-die-outcome\">" + successes + "</div>" );
        var dieFace = results[i];
        if (results[i] === 10) {
            dieFace = 0;
        }
        $("#js-qs-roll-dice").append("<div class=\"css-quickstart-die\" style=\"background-image: url("
            + dieImageUrl + ")\"> <span class=\"css-quickstart-die-val\">" + dieFace + "</span></div>");
    }
    var outcomeText;
    if (outcome > 5) {
        outcomeText = "An Outcome of 6 or more indicates an exceptional success with an additional positive effect.";
        $("#js-qs-action-outcome").html(action.outcomeExceptionalSuccess);
    } else if (outcome > 3) {
        outcomeText = "An Outcome of 4 or 5 indicates a complete success.";
        $("#js-qs-action-outcome").html(action.outcomeCompleteSuccess);
    } else if (outcome > 0) {
        outcomeText = "An Outcome of 1, 2, or 3 indicates a partial success or a success with a complication";
        $("#js-qs-action-outcome").html(action.outcomePartialSuccess);
    } else if (outcome === 0) {
        outcomeText = "An Outcome of 0 is a failure.";
        $("#js-qs-action-outcome").html(action.outcomeFailure);
    } else if (outcome < 0) {
        outcome = outcome + " (botch)"
        outcomeText = "An Outcome of less than 0 is called a botch and indicates that something went horribly wrong.";
        $("#js-qs-action-outcome").html(action.outcomeBotch);
    }
    $("#js-qs-outcome-num").html(outcome);
    $("#js-qs-outcome-explanation").html(outcomeText);
}

$("#js-qs-roll-button").click(function () {
    rollDice();
})

$("#js-qs-next-action").click(function () {
    currentAction++;
    displayAction(currentAction);
})

$("#js-qs-prev-action").click(function () {
    currentAction--;
    displayAction(currentAction);
})

window.onload = function () {
    displayAction(currentAction);
}
