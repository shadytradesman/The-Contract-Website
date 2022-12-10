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
    $(formContainer).append(compiledTmpl);
    $($(ev.target).attr("data-management-form-id")).val(count + 1);
});

