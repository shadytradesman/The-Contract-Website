var formSubmitting = false;
window.onbeforeunload = function() {
    if (formSubmitting) {
    } else {
        return true;
    }
};
var setFormSubmitting = function() { formSubmitting = true; };

$(document).on('click','.js-add-element', function(ev){
    let formContainer = $(ev.target).parent().prev(".js-element-form-container");
    let template = $("#" + $(ev.target).attr("data-template-id")).html();
    let count = formContainer.children().length;
    let compiledTmpl = template.replace(/__prefix__/g, count);
    let newForm = $(formContainer).append(compiledTmpl);
    $($(ev.target).attr("data-management-form-id")).val(count + 1);
    $(newForm).find("input").each(function() {
        if ($(this).attr("type") != "checkbox") {
            $(this).attr("required", true);
        }
    })
});


$(document).on('change','.js-element-form-container input:checkbox', function(ev){
    let box = $(ev.target);
    let checked = box.is(":checked");
    let container = box.closest(".js-element-form-container");
    if (checked) {
        $(container).find("input").each(function() {
            if ($(this).attr("type") != "checkbox") {
                $(this).attr("required", false);
            }
        })
    } else {
        $(container).find("input").each(function() {
            if ($(this).attr("type") != "checkbox") {
                $(this).attr("required", true);
            }
        })
    }
});

$(function(){
    $(".js-element-form-container input").each(function() {
        if ($(this).attr("type") != "checkbox") {
            $(this).attr("required", true);
        }
    })
})

