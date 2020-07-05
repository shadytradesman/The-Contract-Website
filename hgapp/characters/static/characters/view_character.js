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
            // on successfull creating object
            // 1. clear the form.
            $("#scar-form").trigger('reset');
            // 2. focus to nickname input
            $("#id_description").focus();

            // display the newly friend to table.
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
            // alert the error if any error occured
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
            // alert the error if any error occured
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