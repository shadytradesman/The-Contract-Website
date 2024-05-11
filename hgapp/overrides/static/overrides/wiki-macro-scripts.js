$(document).on("click", ".wiki-entry-collapsible", function(e) {
    let collapseButton = $(e.target).closest('.wiki-entry-collapsible');
    collapseButton.toggleClass("active");
    var content = $(collapseButton).next();
    if (content.is(":visible")) {
      content.hide();
    } else {
      content.show();
    }
});
