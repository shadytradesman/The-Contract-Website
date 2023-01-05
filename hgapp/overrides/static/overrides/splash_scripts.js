function setAffix() {
    const container = $("#js-talent-section");
    $('#js-talent-affix').affix({
      offset: {
        top: function () {
        return (this.top = container.position().top - 50)
         },
        bottom: 0
      }
    });
    $('#js-talent-affix').affix('checkPosition');
}

$(document).ready(function(){
    setAffix();
    $(window).scroll();
 setTimeout(() => {
    setAffix();
    }, 280);
});

$( window ).resize(function() {
  setAffix();
  $(window).scroll();
});

