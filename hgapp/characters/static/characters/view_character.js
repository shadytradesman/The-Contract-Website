// Abilities show/hide
var zeroValVisible = true;
$(document).on("click", "#abilities-toggle", function() {
    var button = $(this);
    if (zeroValVisible) {
        $("[class~=zero-ability]").css("display","none");
        zeroValVisible = false;
    } else {
        $("[class~=zero-ability]").css("display","block");
        zeroValVisible = true;
    }
});

// Limits show/hide
var limitsVisible = false;
$(document).on("click", "#limits-toggle", function() {
    var button = $(this);
    if (limitsVisible) {
        $("#js-limits-compact").css("display","flex");
        $("#js-limits-full").css("display","none");
        limitsVisible = false;
    } else {
        $("#js-limits-compact").css("display","none");
        $("#js-limits-full").css("display","block");
        limitsVisible = true;
    }
});

function updateLimitVisibility() {
    if ($(".js-trauma-entry").length < 2 && $(".js-source").length < 1) {
         $("#js-limits-compact").css("display","none");
         $("#js-limits-full").css("display","block");
         limitsVisible = true;
    } else {
        $("#js-limits-compact").css("display","flex");
        $("#js-limits-full").css("display","none");
        limitsVisible = false;
    }
}

// expandable trauma deletion reasons
$(document).on("click", ".js-expand-next-block", function() {
    var button = $(this);
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
});

//ON DOCUMENT READY
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
    updateHealthDisplay();
    updateMentalForms();
    updateLimitVisibility();
});

// CSRF protection on form
var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$("#id_premade_scar_field").change(function (e) {
    let selectedOption = e.target.options[e.target.selectedIndex];
    if (selectedOption.value.length > 0) {
        $("#id_scar_description").val(selectedOption.text);
        $("#id_scar_system").val(selectedOption.value);
    }
})

var descByName = null;
if (document.getElementById('descByName')) {
    descByName = JSON.parse(document.getElementById('descByName').textContent);
}

$(document).on("change", ".js-premade-element-form select", function (e) {
    let selectedOption = e.target.options[e.target.selectedIndex];
    let nameField = $(e.target).closest(".js-world-element-form").find("#id_name");
    let descField = $(e.target).closest(".js-world-element-form").find("#id_description");
    let systemField = $(e.target).closest(".js-world-element-form").find("#id_system");
    if (selectedOption.value.length > 0) {
        systemField.val(selectedOption.value);
        descField.val(descByName[selectedOption.text]);
        nameField.val(selectedOption.text);
    } else {
        systemField.val("");
        descField.val("");
        nameField.val("");
    }
})

$(".js-premade-trauma-form select").change(function (e) {
    let selectedOption = e.target.options[e.target.selectedIndex];
    if (selectedOption.text in descByName) {
        $("#id_trauma-name").val(selectedOption.text);
        $("#id_trauma-system").val(descByName[selectedOption.text]);
    }
})

// add battle scar
$("#scar-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var delUrl = $(this).attr("data-delete-scar-url");

    $.ajax({
        type: 'POST',
        url: $(this).attr("data-new-scar-url"),
        data: serializedData,
        success: function (response) {
            $("#scar-form").trigger('reset');
            $("#id_scar_description").focus();

            var instance = JSON.parse(response["instance"]);
            var fields = instance[0]["fields"];
            delUrl = delUrl.replace(/scarIdJs/g, JSON.parse(response["id"]));
            var tmplMarkup = $('#scar-template').html();
            var compiledTmpl = tmplMarkup.replace(/__description__/g, fields["description"||""]);
            var compiledTmpl = compiledTmpl.replace(/__system__/g, fields["system"||""]);
            var compiledTmpl = compiledTmpl.replace(/__delUrl__/g, delUrl);
            $("#js-scar-container").append(
                compiledTmpl
            )
            $("#js-no-scars").remove();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

// delete battle scar
$("#js-scar-container").on("submit",".js-delete-scar-form", function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var scarForm = $(this);
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-del-scar-url"),
        data: serializedData,
        success: function (response) {
            scarForm.parent().remove();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

// add trauma
$("#trauma-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var delUrl = $(this).attr("data-delete-trauma-url");
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-new-trauma-url"),
        data: serializedData,
        success: function (response) {
            $("#trauma-form").trigger('reset');
            $("#id_trauma-system").focus();

            // display the newly friend to table.
            delUrl = delUrl.replace(/traumaIdJs/g, JSON.parse(response["id"]));
            delWithXpUrl = delUrl.replace(/useXpJs/g, "T");
            delWithoutXpUrl = delUrl.replace(/useXpJs/g, "F");
            var tmplMarkup = $('#trauma-template').html();
            var compiledTmpl = tmplMarkup.replace(/__name__/g, response["name"]);
            var compiledTmpl = compiledTmpl.replace(/__system__/g, response["system"]);
            var compiledTmpl = compiledTmpl.replace(/__delUrlExp__/g, delWithXpUrl);
            var compiledTmpl = compiledTmpl.replace(/__delUrlNoExp__/g, delWithoutXpUrl);
            $("#js-trauma-container").append(
                compiledTmpl
            )
            $("#js-no-traumas").remove();
            updateLimitVisibility();
        },
        error: function (response) {
            console.log(response);
            // alert the error if any error occured
            alert(response["responseJSON"]["error"]);
        }
    })
})

// delete trauma
$("#js-trauma-container").on("submit",".js-delete-trauma-form", function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var traumaForm = $(this);
    traumaForm.parent().find("input").prop("disabled", true);
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-del-trauma-url"),
        data: serializedData,
        success: function (response) {
            traumaForm.parent().parent().parent().remove();
            updateLimitVisibility();
        },
        error: function (response) {
            console.log(response);
            // alert the error if any error occured
            alert(response["responseJSON"]["error"]);
        }
    })
})

// injury inc / dec buttons
function makeIncDecButtons(element) {
    element.append('<span class="inc val-adjuster btn btn-default btn-xs"><i class="fa fa-plus"></i></span>');
    element.prepend('<span class="dec val-adjuster btn btn-default btn-xs"><i class="fa fa-minus"></i></span>');
}

$(makeIncDecButtons($("span[class~='js-injury-form']")));

$(document).on("click", ".val-adjuster", function() {
  var button = $(this);
  var oldValue = button.parent().find("input").val();
  var newValue = 0;
  if (button.hasClass("inc")) {
      if (oldValue < 15) {
        newValue = parseFloat(oldValue) + 1;
      }
      else {
	     newValue = 15;
	  }
	} else {
    if (oldValue > 0) {
      newValue = parseFloat(oldValue) - 1;
    } else {
      newValue = 0;
    }
  }
  button.parent().find("input").val(newValue); // NOTE: this causes issues if there is more than one input child.
});

// add injury
$(".injury-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var stabilizeUrl = $(this).attr("data-stabilize-injury-url");
    var incUrl = $(this).attr("data-inc-injury-url");
    var decUrl = $(this).attr("data-dec-injury-url");
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-new-injury-url"),
        data: serializedData,
        success: function (response) {
            $("#injury-form").trigger('reset');
            $("#id_description").focus();

            var instance = JSON.parse(response["instance"]);
            var fields = instance[0]["fields"];
            let injuryId = JSON.parse(response["id"]);
            stabilizeUrl = stabilizeUrl.replace(/injuryIdJs/g, injuryId);
            incUrl = incUrl.replace(/injuryIdJs/g, injuryId);
            decUrl = decUrl.replace(/injuryIdJs/g, injuryId);
            let stabilityTemplate = $("#injury-stabilization-template").html();
            if (response["severity"] < 4) {
                stabilityTemplate = "";
            }
            let tmplMarkup = $('#injury-template').html();
            let compiledTmpl = tmplMarkup.replace(/__description__/g, fields["description"||""]);
            compiledTmpl = compiledTmpl.replace(/__stabilization__/g, stabilityTemplate);
            compiledTmpl = compiledTmpl.replace(/__stabilizeUrl__/g, stabilizeUrl);
            compiledTmpl = compiledTmpl.replace(/__incUrl__/g, incUrl);
            compiledTmpl = compiledTmpl.replace(/__decUrl__/g, decUrl);
            compiledTmpl = compiledTmpl.replace(/__severity__/g, response["severity"]);
            $("#js-injury-container").append(
                compiledTmpl
            )
            $("#js-no-injuries").remove();
            updateHealthDisplay();
            $('[data-toggle="tooltip"]').tooltip({
                trigger : 'hover'
            });
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

// inc/dec/stabilize injury
$("#js-injury-container").on("submit",".js-edit-injury-form", function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var injuryForm = $(this);
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-edit-injury-url"),
        data: serializedData,
        success: function (response) {
            let severity = response["severity"];
            if (severity <= 0) {
                injuryForm.parent().parent().remove();
            } else {
                $(injuryForm.siblings(".injury-severity")[0]).text(severity);
            }
            if (response["stabilized"]) {
                injuryForm.closest(".js-injury-stabilization-status").html($("#stabilized-icon-template").html());
                $('[data-toggle="tooltip"]').tooltip({
                    trigger : 'hover'
                });
            }
            updateHealthDisplay();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

const numBodyLevels = JSON.parse(document.getElementById('numBodyLevels').textContent);
const numMindLevels = JSON.parse(document.getElementById('numMindLevels').textContent);
var mindDamage = JSON.parse(document.getElementById('mindDamage').textContent);

// health display
function updateHealthDisplay() {
    var numInjuries = 0;
    var highestSeverity = 0;
    $(".injury-severity").each(function() {
        var severity = parseInt($(this).text());
        if (severity > highestSeverity) {
            highestSeverity = severity;
        }
        numInjuries ++;
    });
    var damageValue = highestSeverity + numInjuries - 1;
    if (damageValue > 0) {
        $("#js-wound-container").show();
        $("#js-worst-injury").html(highestSeverity);
        $("#js-num-other-injuries").html(numInjuries - 1);
    } else {
        $("#js-wound-container").hide();
    }
    var damageValue = damageValue < 0 ? 0 : damageValue;
    var i;
    var bodyPenalty = 0;
    for (i = 0; i < numBodyLevels + 1; i++) {
        var content = damageValue > i ? '<i class="fa fa-square fa-2x" ></i>' : '<i class="fa fa-square-o fa-2x" ></i>';
        $("#js-body-" + i).html(content);
        if (damageValue > i) {
            var penalty = $(".js-penalty-body-" + i);
            console.log("penalty = " + penalty.html());
            if (penalty.html()) {
                var penalty = penalty.html().trim();
                var penNum = parseInt(penalty);
                if (isNaN(penNum)) {
                    bodyPenalty = penalty;
                } else {
                    bodyPenalty = penNum;
                }
            }
        }
    }
    var mindPenalty = 0;
    for (i = 0; i < numMindLevels + 1; i++) {
        var content = mindDamage > i ? '<i class="fa fa-square fa-2x" ></i>' : '<i class="fa fa-square-o fa-2x" ></i>';
        $("#js-mind-" + i).html(content);
        if (mindDamage > i) {
            var penalty = $(".js-penalty-mind-" + i);
            if (penalty.html()) {
                var penalty = penalty.html().trim();
                var penNum = parseInt(penalty);
                if (isNaN(penNum)) {
                    mindPenalty = penalty;
                } else {
                    mindPenalty = penNum;
                }
            }
        }
    }
    // update penalty
    var penaltyContent;
    if (isNaN(mindPenalty)) {
        penaltyContent = mindPenalty;
        $(".js-roll-penalty").hide();
    } else if (isNaN(bodyPenalty)) {
        penaltyContent = bodyPenalty;
        $(".js-roll-penalty").hide();
    } else {
        penaltyContent = mindPenalty + bodyPenalty;
        if (penaltyContent < 0) {
            $(".js-roll-penalty").each(function () {
                var penaltyMultiplier = parseInt($(this).attr('data-penalty-multiplier'));
                penaltyMultiplier = penaltyMultiplier ? penaltyMultiplier: 1;
                $(this).html(penaltyContent * penaltyMultiplier);
            })
            $(".js-roll-penalty").show();
        } else {
            $(".js-roll-penalty").hide();
        }
    }
    $("#js-penalty-box").html(penaltyContent);

    if (damageValue > numBodyLevels) {
        $("#js-dead-box").css("display","block");
    } else {
        $("#js-dead-box").css("display","none");
    }
}

function updateMentalForms() {
    $("#exert-mind-val").val(mindDamage + 1);
    $("#recover-mind-val").val(mindDamage <=0 ? 0 : mindDamage > numMindLevels ? numMindLevels : mindDamage -1);
}

// Exert mind
$("#exert-mind-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-url"),
        data: serializedData,
        success: function (response) {
            mindDamage = parseInt($("#exert-mind-val").val());
            updateMentalForms();
            updateHealthDisplay();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

// Recover mind
$("#recover-mind-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-url"),
        data: serializedData,
        success: function (response) {
            mindDamage = parseInt($("#recover-mind-val").val());
            updateMentalForms();
            updateHealthDisplay();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

var sourceValues = JSON.parse(document.getElementById('sourceValues').textContent);
const sourceFullIcon = ' <i class="fa fa-circle fa-2x"></i> '
const sourceEmptyIcon = ' <i class="fa fa-circle-o fa-2x"></i> '

function updateSourceDisplay() {
    Object.keys(sourceValues).forEach(function(key) {
        content = "";
        var i =0;
        var currentVal = parseInt(sourceValues[key][0]);
        var maxVal = parseInt(sourceValues[key][1]);
        if (currentVal > maxVal) {
            currentVal = maxVal;
            sourceValues[key][0] = maxVal;
        }
        for (i=0; i < currentVal; i++) {
            content = content + sourceFullIcon;
        }
        for (i=sourceValues[key][0]; i < maxVal; i++) {
            content = content + sourceEmptyIcon;
        }
        $("#js-source-" + key).find(".js-source-display").html(content);
        $("#js-source-" + key).find(".js-source-refill").text(sourceValues[key][2]);
        if (sourceValues[key][3]) {
            $("#js-source-" + key).find(".js-source-refill-cont-professional").show();
            $("#js-source-" + key).find(".js-source-refill-professional").text(sourceValues[key][3]);
        }
        if (sourceValues[key][4]) {
            $("#js-source-" + key).find(".js-source-refill-cont-veteran").show();
            $("#js-source-" + key).find(".js-source-refill-veteran").text(sourceValues[key][4]);
        }
        console.log(key, sourceValues[key]);
    });
}

function updateSourceForms() {
    $(".js-source-dec-form").each(function(){
        var sourceId = $(this).attr("data-source-id");
        var currentVal = sourceValues[sourceId][0];
        var newValue = currentVal == 0 ? currentVal : currentVal - 1;
        $(this).children(".js-source-val").val(newValue);
    });
    $(".js-source-inc-form").each(function(){
        var sourceId = $(this).attr("data-source-id");
        var currentVal = parseInt(sourceValues[sourceId][0]);
        var newValue = parseInt(sourceValues[sourceId][1]) == currentVal ? currentVal : currentVal + 1;
        $(this).children(".js-source-val").val(newValue);
    });
}

$(updateSourceDisplay());
$(updateSourceForms());

//update source
$(".js-source-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var newValue = $(this).children(".js-source-val").val();
    var sourceId = $(this).attr("data-source-id");
    if (newValue <= sourceValues[sourceId][1] && newValue >= 0 ) {
        $.ajax({
            type: 'POST',
            url: $(this).attr("data-url"),
            data: serializedData,
            success: function (response) {
                sourceValues[sourceId][0] = newValue;
                updateSourceForms();
                updateSourceDisplay();
            },
            error: function (response) {
                console.log(response);
                alert(response["responseJSON"]["error"]);
            }
        })
    }
})


// Bio
var bioValue = JSON.parse(document.getElementById('bio').textContent);
$($("#js-bio-form").children("textarea").val(bioValue));
$(document).on("click", "#js-edit-bio-button", function(){
    $("#js-bio-text").css("display","none");
    $("#js-edit-bio-button").css("display","none");
    $("#js-bio-form").css("display","block");
    $("#js-bio-expand-button").css("display","none");
});

$("#bio-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-post-url"),
        data: serializedData,
        success: function (response) {
            var instance = response["bio"];
            var conv = new showdown.Converter();
            $("#js-bio-form").children("textarea").val(instance);
            // This is safe only because the only people to see this output are the ones who submitted it.
            $("#js-bio-text").html(conv.makeHtml(instance));
            $("#js-bio-text").css("display","block");
            $("#js-edit-bio-button").css("display","inline-block");
            $("#js-bio-form").css("display","none");
            $("#js-bio-expand-button").css("display","inline-block");
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})


// Notes form
var notesValue = JSON.parse(document.getElementById('notes').textContent);
$($("#js-notes-form").children("textarea").val(notesValue));
$(document).on("click", "#js-edit-notes-button", function(){
    $("#js-notes-text").css("display","none");
    $("#js-edit-notes-button").css("display","none");
    $("#js-notes-form").css("display","block");
    $("#js-notes-expand-button").css("display","none");
});

$("#notes-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-post-url"),
        data: serializedData,
        success: function (response) {
            var instance = response["notes"];
            var conv = new showdown.Converter();
            $("#js-notes-form").children("textarea").val(instance);
            // This is safe only because the only people to see this output are the ones who submitted it.
            $("#js-notes-text").html(conv.makeHtml(instance));
            $("#js-notes-text").css("display","block");
            $("#js-edit-notes-button").css("display","inline-block");
            $("#js-notes-form").css("display","none");
            $("#js-notes-expand-button").css("display","inline-block");
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

function copyToClipboard(elem) {
	  // create hidden text element, if it doesn't already exist
    var targetId = "_hiddenCopyText_";
    var isInput = elem.tagName === "INPUT" || elem.tagName === "TEXTAREA";
    var origSelectionStart, origSelectionEnd;
    if (isInput) {
        // can just use the original source element for the selection and copy
        target = elem;
        origSelectionStart = elem.selectionStart;
        origSelectionEnd = elem.selectionEnd;
    } else {
        // must use a temporary form element for the selection and copy
        target = document.getElementById(targetId);
        if (!target) {
            var target = document.createElement("textarea");
            target.style.position = "absolute";
            target.style.left = "-9999px";
            target.style.top = "0";
            target.id = targetId;
            document.body.appendChild(target);
        }
        target.textContent = elem.textContent;
    }
    // select the content
    var currentFocus = document.activeElement;
    target.focus();
    target.setSelectionRange(0, target.value.length);

    // copy the selection
    var succeed;
    try {
    	  succeed = document.execCommand("copy");
    } catch(e) {
        succeed = false;
    }
    // restore original focus
    if (currentFocus && typeof currentFocus.focus === "function") {
        currentFocus.focus();
    }

    if (isInput) {
        // restore prior selection
        elem.setSelectionRange(origSelectionStart, origSelectionEnd);
    } else {
        // clear temporary content
        target.textContent = "";
    }
    return succeed;
}

window.onload = function () {
    if (document.getElementById("copySecretLink")) {
        document.getElementById("copySecretLink").addEventListener("click", function() {
        copyToClipboard(document.getElementById("secretCopyField"));});
        document.getElementById("copyShareLink").addEventListener("click", function() {
        copyToClipboard(document.getElementById("shareCopyField"));});
    }
};
