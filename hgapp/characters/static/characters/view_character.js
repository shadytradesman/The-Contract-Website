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