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
