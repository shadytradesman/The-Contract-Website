var formSubmitting = false;
window.onbeforeunload = function() {
    if (formSubmitting) {
    } else {
        return true;
    }
};
var setFormSubmitting = function() {
    formSubmitting = true;
    $("#question-submit").prop('disabled', true);
};
