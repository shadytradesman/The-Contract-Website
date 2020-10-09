$.fn.followTo = function (pos) {
    var $this = this,
        $window = $(window);

    $window.scroll(function (e) {
        if ($window.scrollTop() + $window.height() > pos - 51) {
            $this.css({
                position: 'absolute',
                top: pos - $window.height() + 50
            });
        } else {
            $this.css({
                position: 'fixed',
                top: 50
            });
        }
    });
};

function setAffix() {
    const $frontBullets = $('#css-front-bullets-section');
    const textHeight = $frontBullets.position().top + $frontBullets.outerHeight(true);
    $('.css-art-front-punk').followTo(textHeight);
}

$(document).ready(function(){
    setAffix();
    $(window).scroll();
});

$( window ).resize(function() {
  setAffix();
  $(window).scroll();
});