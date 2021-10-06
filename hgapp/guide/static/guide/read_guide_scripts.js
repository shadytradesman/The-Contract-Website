$('body').scrollspy({ target: '#js-guide-index' })

function setAffix() {
    $('#js-guide-index').affix({
      offset: {
        top: 0,
        bottom: document.body.scrollHeight - 50,
      }
    })
}

$(document).ready(function(){
    $(window).scroll();
});

var oddSpy = false;
$('body').on('activate.bs.scrollspy', function () {
    // this triggers twice because the guidebook is a nested nav list. We only want the first one.
    oddSpy = !oddSpy;
    if (oddSpy) {
        return;
    }
    target = $("#js-guide-index .active").get(1);
    /* vertical scroll fix */
    if (target.getBoundingClientRect().bottom > window.innerHeight) {
        // scroll at bottom
        target.scrollIntoView(false);
    }
    if (target.getBoundingClientRect().top < 50) {
        // scroll at top
        target.scrollIntoView();
    }
    if ($(target).hasClass("js-first-section")) {
        $("#js-guide-index").scrollTop(0);
    }
    if ($(target).hasClass("js-last-section")) {
        $("#js-guide-index").scrollTop($("#js-guide-index")[0].scrollHeight);
    }
    if (target.getBoundingClientRect().left <0 ) {
        target.scrollIntoView(false);
    }
    if (target.getBoundingClientRect().right > window.innerWidth) {
        target.scrollIntoView();
    }
    /* horizontal scroll fix */
    // TODO: horizontal scroll fix
})