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
    if (target.getBoundingClientRect().bottom > window.innerHeight - 50) {
        target.scrollIntoView(false);
        console.log("scroll bottom");
    }

    if (target.getBoundingClientRect().top < 50) {
        target.scrollIntoView();
        console.log("scroll top");
    }
})