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
    // correct scroll when all images loaded.
    Promise.all(Array.from(document.images).filter(img => !img.complete).map(img => new Promise(resolve => { img.onload = img.onerror = resolve; }))).then(() => {
        $(window).scroll();
    });
});

var oddSpy = false;
$('body').on('activate.bs.scrollspy', function () {
    // this triggers twice because the guidebook is a nested nav list. We only want the first one.
    oddSpy = !oddSpy;
    if (oddSpy) {
        return;
    }
    scrollToc();
})

function scrollToc() {
    target = $("#js-guide-index .active").get(1);
    /* vertical scroll fix */
    if (target.getBoundingClientRect().bottom > window.innerHeight) {
        // scroll at bottom
        target.scrollIntoView({block: "end", inline: "nearest"});
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
    if (target.getBoundingClientRect().left < 0 ) {
        target.scrollIntoView({block: "end", inline: "center"});
    }
    if (target.getBoundingClientRect().right > window.innerWidth) {
        target.scrollIntoView({block: "start", inline: "center"});
    }
}

function toggleToc() {
    const index = $("#js-guide-index");
    const horizontalTocClass = "horizontal-toc";
    if (index.hasClass(horizontalTocClass)) {
        index.removeClass(horizontalTocClass);
        $(document.body).addClass("noscroll");
    } else {
        index.addClass(horizontalTocClass);
        $(document.body).removeClass("noscroll");
    }
    scrollToc();
}

$(".guide-toc a").on("click", function() {
    const index = $("#js-guide-index");
    const horizontalTocClass = "horizontal-toc";
    index.addClass(horizontalTocClass);
    $(document.body).removeClass("noscroll");
    scrollToc();
})
