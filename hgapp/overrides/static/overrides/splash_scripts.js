function setAffix() {
    const $window = $(window);
    const $home = $('#home');
    const homeEnd =  document.body.scrollHeight - $home.position().top - $home.outerHeight(true);

}

function setAffix() {
    const container = $("#js-talent-affix");
    $('#js-talent-affix').affix({
      offset: {
        top: container.position().top - 50
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

