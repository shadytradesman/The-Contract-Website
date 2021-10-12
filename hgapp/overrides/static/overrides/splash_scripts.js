function setAffix() {
    const $window = $(window);
    const $home = $('#home');
    const homeEnd =  document.body.scrollHeight - $home.position().top - $home.outerHeight(true);

    $('.css-art-front-punk').affix({
      offset: {
        top: -50,
        bottom:  homeEnd - 50,
      }
    })
}

$(document).ready(function(){
    setAffix();
    $(window).scroll();
});

$( window ).resize(function() {
  setAffix();
  $(window).scroll();
});

