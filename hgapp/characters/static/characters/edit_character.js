// Enable navigation prompt
var isDirty = false;
var formSubmitting = false;
window.onbeforeunload = function() {
    if (formSubmitting || !isDirty) {
    } else {
        return true;
    }
};
var setFormSubmitting = function() { formSubmitting = true; isDirty=false; };


function makeIncDecButtons(element, type) {
    element.append('<span class="inc val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-plus"></i></span>');
    element.prepend('<span class="dec val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-minus"></i></span>');
}

$(makeIncDecButtons($("span[class~='ability-form']"), "ability"));
$(makeIncDecButtons($("span[class~='source-form']"), "source"));

function handleAdjusterPress(button) {
    isDirty = true;
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

$(document).on("click", ".val-adjuster-source", function() {
  handleAdjusterPress($(this));
  updateSourceExp($(this).parent());
});

$(document).on("input keyup mouseup", ".ability-value-input", function() {
    updateAbilityExp($(this).parent());
});

$(document).on("input keyup mouseup", ".source-value-input", function() {
    updateSourceExp($(this).parent());
});

// Secondary ability creation / destruction
$(document).on('change','[class~=sec-ability-name]', function(ev){
    isDirty = true;
    var numSkills = $('[class~=ability-value-input]').length - 1; // subtract empty form
    var emptySecondaries = $('[class~=sec-ability-name]')
        .filter(function() {return !this.value && !$(this.parentElement).is(":hidden");});
    var numEmptySecondaries = emptySecondaries.length;
    if (numEmptySecondaries > 1) {
        var sec = emptySecondaries[0];
        $(sec).siblings(".ability-form").children(".ability-value-input").val(0);
        console.log($(sec).siblings(".ability-form").children(".ability-value-input"));
        updateAbilityExp($(sec).siblings(".ability-form"));
        updateExpTotals();
        $(sec.parentElement).hide();
    } else if (numEmptySecondaries == 0) {
        var secondaryId = numSkills + 1;
        var tmplMarkup = $('#sec-ability-template').html();
        var compiledTmpl = tmplMarkup.replace(/__prefix__/g, secondaryId);
        var elem = $("#abilities-forms").append(compiledTmpl);
        makeIncDecButtons($("span[id=secondary-ability-form-" + secondaryId + "]"), "ability");
        $('#id_abilities-TOTAL_FORMS').attr('value', numSkills + 1);
    }
});

// toggle-y buttons
$('.btn').button();
$(".btn").mouseup(function(){
    $(this).blur();
})

// Quirk creation / destruction
//NOTE: instead of removing the quirk, perhaps just hide it? Can use is_selected() to figure out if it's selected in forms.
$(document).on('change','[id$=-is_selected]', function(ev) {
    isDirty = true;
    var checkbox = $(this);
    updateQuirkExp(checkbox.parents(".quirk-btn"));
    if (checkbox.hasClass("quirk-multiple-False")) {
        return true;
    }
    var checkboxGroup = checkbox.closest(".quirk-group-container");
    var isLiability = checkboxGroup.children("[id^=liability]").length > 0;
    var quirkWord = isLiability ? 'liability' : 'asset';

    var quirkId = checkboxGroup.attr('id').slice(6);
    var count = $('[class~=btn-'+ (isLiability ? "True" : "False") +'-'+ quirkId + ']').length;
    var allThisQuirksButtons = $('[class~=btn-'+ (isLiability ? "True" : "False") +'-'+ quirkId + ']');
    var emptyCheckboxes = allThisQuirksButtons
            .filter(function() {return !$(this).is(".active") && !$(this.parentElement).is(":hidden");});
    console.log(allThisQuirksButtons)
    console.log(emptyCheckboxes)
    var visibleCount =  allThisQuirksButtons
            .filter(function() {return !$(this.parentElement).is(":hidden");})
            .length;
    if (this.checked && visibleCount < 4) {
        if (isLiability) {
            var tmplMarkup = $('#liability-'+quirkId+"-template").html();
        } else {
            var tmplMarkup = $('#asset-'+quirkId+"-template").html();
        }
        var compiledTmpl = tmplMarkup.replace(/__prefix__/g, count);

        checkboxGroup.append(compiledTmpl);
        if (compiledTmpl.includes("wiki-entry-collapsible")) {
                var collapsibleContainer = checkboxGroup.find('[class~=wiki-entry-collapsible]').last()[0];
                setupCollapsibles(collapsibleContainer);
        }
        $('#id_' + quirkWord  + quirkId + '-' + count + '-id').attr('value', quirkId)
        $('#id_' + quirkWord +  quirkId + '-TOTAL_FORMS').attr('value', count+1);
    } else if (!this.checked && (count > 1) && emptyCheckboxes.length>1) {
        checkbox.closest('[id^=' + quirkWord + '-'+quirkId+']').hide();
    }
});

// Limit Warning
$(document).on('change','[id$=-checked]', function(ev){
    isDirty = true;
    var numLimitsSelected = $('input:checked[id$=-checked]').length; // subtract empty form
    var warnDiv = $('[class~=limit-warn]');
    if (numLimitsSelected == 3) {
        warnDiv.css("display","none");
    } else {
        warnDiv.html("<p>All Characters must select exactly <b>3</b> Limits unless they have an Asset or "
                            + "Liability that states otherwise.</p>"
                            + "<p>Number currently selected: <b>" + numLimitsSelected + "</b></p>");
        warnDiv.css("display","block");
    }
});

//////////////////
// EXPERIENCE MANAGEMENT
//////////////////
const expToSpend = JSON.parse(document.getElementById('expToSpend').textContent);
const costs = JSON.parse(document.getElementById('expCosts').textContent)
var expPrice = 0;

function updateExpTotals() {
    updateExpPrice();
    $(".js-remaining-exp").text(expToSpend + expPrice);
    $("#js-starting-exp").text(expToSpend);
    $("#js-spent-exp").text(expPrice > 0 ? "+" + expPrice : expPrice == 0? "-" + expPrice : expPrice);
    if (expToSpend + expPrice < 0) {
        $(".js-exp-warn").css("display","block");
    } else {
        $(".js-exp-warn").css("display","none");
    }
}

function updateExpPrice() {
  expPrice = 0;
  $(".js-experience-cost-value").each(function() {
        expPrice = expPrice + parseInt($(this).text());
  });
}

$(document).ready(function(){
    updateExpTotals();
});

// update attribute exp values
$(document).on("change", "[id^=id_attributes]", function() {
    var value = $(this).children("option:selected").attr("value");
    var expCostDiv = $(this).siblings(".css-experience-cost");
    var initial = expCostDiv.attr("data-initial-attr-value");
    var cost = calculateAttrChangeCost(initial, value);
    var price = -cost;
    var priceText = price > 0 ? "+" + price : price;
    expCostDiv.children(".js-experience-cost-value").text(priceText);
    if (cost != 0) {
        expCostDiv.css("display","inline");
    } else {
        expCostDiv.css("display","none");
    }
    updateExpTotals();
});

function calculateAttrChangeCost(oldValue, newValue) {
    oldValue = parseInt(oldValue);
    newValue = parseInt(newValue);
    return ((newValue - oldValue) * (oldValue + newValue - 1) / 2) * parseInt(costs["EXP_ADV_COST_ATTR_MULTIPLIER"]);
}

function calculateSourceChangeCost(oldValue, newValue) {
    oldValue = parseInt(oldValue);
    newValue = parseInt(newValue);
    return ((newValue - oldValue) * (oldValue + newValue - 1) / 2) * parseInt(costs["EXP_ADV_COST_SOURCE_MULTIPLIER"]);
}

function calculateAbilityChangeCost(oldValue, newValue) {
    oldValue = parseInt(oldValue);
    newValue = parseInt(newValue);
    var advMultiplier = parseInt(costs["EXP_ADV_COST_SKILL_MULTIPLIER"]);
    if (oldValue == 0 && newValue != 0) {
        initial_cost = 2;
    }
    else if (oldValue != 0 && newValue == 0) {
        initial_cost = -2;
    }
    else {
        initial_cost = 0;
    }
    return ((newValue - oldValue) * (oldValue + newValue - 1) / 2) * advMultiplier + initial_cost;
}

function updateAbilityExp(valueSpanElement) {
    console.log("abilityxp");
    console.log(valueSpanElement);
    var value = valueSpanElement.children(".ability-value-input").val();
    if (!value) {
        console.log("nan out");
        return;
    }
    console.log(value);
    var initial = valueSpanElement.attr("data-initial-val");
    initial = initial ? initial : 0;
    console.log(initial);
    var cost = calculateAbilityChangeCost(initial, value);
    var expCostDiv = valueSpanElement.siblings(".css-experience-cost");
    console.log(expCostDiv);
    var price = -cost;
    var priceText = price > 0 ? "+" + price : price;
    expCostDiv.children(".js-experience-cost-value").text(priceText);
    if (cost != 0) {
        expCostDiv.css("display","inline");
    } else {
        expCostDiv.css("display","none");
    }
    updateExpTotals();
}

const EXP_COST_QUIRK_MULTIPLIER = parseInt(costs["EXP_COST_QUIRK_MULTIPLIER"]);
function updateQuirkExp(quirkButtonDiv) {
    console.log(quirkButtonDiv);
    var initialActive = quirkButtonDiv.attr("data-initial") == "True";
    console.log("initialActive: " + initialActive);
    var active = $(quirkButtonDiv).hasClass("active");
    console.log("active: " + active);
    var quirkValue = $(quirkButtonDiv).find(".js-quirk-value").text();
    console.log("qvalue: " + quirkValue);
    var quirkIsLiability = $(quirkButtonDiv).attr("data-liability") == "True";
    console.log("is liability: " + quirkIsLiability);
    var cost;
    if (active == initialActive) {
        cost = 0;
    } else {
        expVal = EXP_COST_QUIRK_MULTIPLIER * quirkValue;
        cost = active == quirkIsLiability ? expVal : -expVal;
    }
    console.log("cost: " + cost);
    var expCostDiv = quirkButtonDiv.find(".css-experience-cost")
    quirkButtonDiv.find(".js-experience-cost-value").text(cost);
    console.log(expCostDiv);
    if (cost != 0) {
        expCostDiv.css("display","inline");
    } else {
        expCostDiv.css("display","none");
    }
    updateQuirkCatExpTotals();
    updateExpTotals();
}

function updateQuirkCatExpTotals() {
    function updateQuirkCatExpTotal(category) {
        var expPrice = 0;
        $("#" + category).find(".js-experience-cost-value").each(function() {
            expPrice = expPrice + parseInt($(this).text());
        });
        var expCat = $("#" + "js-quirk-cat-" + category + "-exp-val");
        var priceText = expPrice > 0 ? "+" + expPrice : expPrice;
        expCat.text(priceText);
        if (expPrice != 0) {
            expCat.parent().css("display","inline");
        } else {
            expCat.parent().css("display","none");
        }
    };
    updateQuirkCatExpTotal("physical");
    updateQuirkCatExpTotal("background");
    updateQuirkCatExpTotal("mental");
    updateQuirkCatExpTotal("restricted");
}

function updateSourceExp(valueSpanElement) {
    console.log("source xp");
    console.log(valueSpanElement);
    var value = valueSpanElement.children(".source-value-input").val();
    if (!value) {
        console.log("nan out");
        return;
    }
    console.log(value);
    var initial = valueSpanElement.attr("data-initial-val");
    initial = initial ? initial : 0;
    console.log(initial);
    var cost = calculateSourceChangeCost(initial, value);
    var expCostDiv = valueSpanElement.siblings(".css-experience-cost");
    console.log(expCostDiv);
    var price = -cost;
    var priceText = price > 0 ? "+" + price : price;
    expCostDiv.children(".js-experience-cost-value").text(priceText);
    if (cost != 0) {
        expCostDiv.css("display","inline");
    } else {
        expCostDiv.css("display","none");
    }
    updateExpTotals();
}

$(document).ready(function(){
    if (showTutorial) {
        $('#tutorialModal').modal({});
    }
});