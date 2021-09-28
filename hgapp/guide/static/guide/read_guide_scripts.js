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

$('body').on('activate.bs.scrollspy', function () {
    target = $("#js-guide-index .active").get(0);
    /* vertical scroll fix */
    if (target.getBoundingClientRect().bottom > window.innerHeight - 50) {
        target.scrollIntoView(false);
    }
    if (target.getBoundingClientRect().top < 50) {
        target.scrollIntoView();
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