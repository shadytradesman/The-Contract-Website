var zeroValVisible = false;
$(document).on("click", "#abilities-toggle", function() {
    var button = $(this);
    if (zeroValVisible) {
        $("[class~=zero-ability]").css("display","none");
        button.html("Show all Primaries");
        zeroValVisible = false;
    } else {
        $("[class~=zero-ability]").css("display","block");
        button.html("Hide Unused Abilities");
        zeroValVisible = true;
    }
});

$(document).on("click", ".js-trauma-del", function() {
    var button = $(this);
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
});

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
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
            $("#id_description").focus();

            var instance = JSON.parse(response["instance"]);
            var fields = instance[0]["fields"];
            delUrl = delUrl.replace(/scarIdJs/g, JSON.parse(response["id"]));
            var tmplMarkup = $('#scar-template').html();
            var compiledTmpl = tmplMarkup.replace(/__description__/g, fields["description"||""]);
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
            scarForm.parent().parent().remove();
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
            $("#id_trauma-description").focus();

            // display the newly friend to table.
            delUrl = delUrl.replace(/traumaIdJs/g, JSON.parse(response["id"]));
            var tmplMarkup = $('#trauma-template').html();
            var compiledTmpl = tmplMarkup.replace(/__description__/g, response["description"]);
            var compiledTmpl = compiledTmpl.replace(/__delUrlExp__/g, delUrl + "T");
            var compiledTmpl = compiledTmpl.replace(/__delUrlNoExp__/g, delUrl + "F");
            $("#js-trauma-container").append(
                compiledTmpl
            )
            $("#js-no-traumas").remove();

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
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-del-trauma-url"),
        data: serializedData,
        success: function (response) {
            traumaForm.parent().parent().parent().remove();
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
$("#injury-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var delUrl = $(this).attr("data-delete-injury-url");
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-new-injury-url"),
        data: serializedData,
        success: function (response) {
            $("#injury-form").trigger('reset');
            $("#id_description").focus();

            var instance = JSON.parse(response["instance"]);
            var fields = instance[0]["fields"];
            delUrl = delUrl.replace(/injuryIdJs/g, JSON.parse(response["id"]));
            var tmplMarkup = $('#injury-template').html();
            var compiledTmpl = tmplMarkup.replace(/__description__/g, fields["description"||""]);
            var compiledTmpl = compiledTmpl.replace(/__delUrl__/g, delUrl);
            var compiledTmpl = compiledTmpl.replace(/__severity__/g, response["severity"]);
            $("#js-injury-container").append(
                compiledTmpl
            )
            $("#js-no-injuries").remove();
            updateHealthDisplay();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

// delete battle injury
$("#js-injury-container").on("submit",".js-delete-injury-form", function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var injuryForm = $(this);
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-del-injury-url"),
        data: serializedData,
        success: function (response) {
            injuryForm.parent().parent().remove();
            updateHealthDisplay();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})


const numBodyLevels = JSON.parse(document.getElementById('numBodyLevels').textContent);

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
    var damageValue = highestSeverity + numInjuries -1;
    var damageValue = damageValue < 0 ? 0 : damageValue;
    var i;
    var bodyPenalty = 0;
    for (i = 0; i < numBodyLevels + 1; i++) {
        content = damageValue > i ? '<i class="fa fa-square fa-2x" ></i>' : '<i class="fa fa-square-o fa-2x" ></i>';
        $("#js-body-" + i).html(content);
        if (damageValue > i) {
            var penalty = $(".js-penalty-body-" + i);
            console.log("penalty = " + penalty.html());
            if (penalty.html()) {
                var penalty = penalty.html().trim();
                var penNum = parseInt(penalty);
                console.log(penNum);
                if (isNaN(penNum)) {
                    bodyPenalty = penalty;
                    penaltyDecided = true;
                    console.log("decided" + penalty);
                } else {
                    bodyPenalty = penNum;
                }
            }
        }
    }

    // update penalty
    $("#js-penalty-box").html(bodyPenalty)

}