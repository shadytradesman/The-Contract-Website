$(function() {
    if (screen.width > 767) {
        let collapsibles = $(".js-auto-in");
        collapsibles.each(function() {
            $( this ).addClass( "in" );
        });
        $(".css-accordion-header-button").each(function() {
            $( this ).addClass( "collapsed" );
        })
    }
});
