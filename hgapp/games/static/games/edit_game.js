$(function(){
    function handleScenarioChange() {
        var $this = $(this);
        var scenarioId = $this.val();
        if (scenarioId) {
            $("#js-scenario-title").hide();
        } else {
            $("#js-scenario-title").show();
        }
    }
    $("#id_scenario").change(handleScenarioChange);
    $("#id_scenario").change();
});

/* + - BUTTONS FOR MAX PLAYERS */
function makeIncDecButtons(element, type) {
    element.append('<span class="inc val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-plus"></i></span>');
    element.prepend('<span class="dec val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-minus"></i></span>');
}

$(makeIncDecButtons($("span[class~='ability-form']"), "ability"));

function handleAdjusterPress(button) {
    var oldValue = parseInt(button.parent().find("input").val());
    var newValue = 0;
    var maxValue = parseInt(button.parent().attr("data-max-value"));
    var minValue = parseInt(button.parent().attr("data-min-value"));

    if (button.hasClass("inc")) {
        if (oldValue < maxValue) {
            newValue = oldValue + 1;
        }
        else {
            newValue = maxValue;
        }
    } else {
        if (oldValue > minValue) {
            newValue = oldValue - 1;
        } else {
            newValue = minValue;
        }
    }
    button.parent().find("input").val(newValue); // NOTE: this causes issues if there is more than one input child.
}

$(document).on("click", ".val-adjuster-ability", function() {
    handleAdjusterPress($(this));
    updateAbilityExp($(this).parent());
});

$(document).on("input keyup mouseup", ".ability-value-input", function() {
    isDirty = true;
    updateAbilityExp($(this).parent());
});
