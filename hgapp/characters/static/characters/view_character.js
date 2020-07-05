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