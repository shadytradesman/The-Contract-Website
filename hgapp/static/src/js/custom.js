/* Tooltips */
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});

/* Power badge stuff */
$(document).on("click", ".power-badge a", function(e) {
   e.stopPropagation();
});

/* Expandables */
$(function(){
    const collapsedClass = "js-expandable-collapsed";

    function handleExpandClick() {        // define event handler
        var $this = $(this);
        if ($this.hasClass(collapsedClass)){
            $this.removeClass(collapsedClass);
        } else {
            $this.addClass(collapsedClass);
        }
    }
    $(".expandable-outer").click(handleExpandClick);
    $(".expandable-outer a").click(function(event){
      event.stopPropagation();
    });
});

