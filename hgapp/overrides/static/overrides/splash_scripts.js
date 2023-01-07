function setAffix() {
    $('.js-affix-image').each(function( index, value ) {
        let container = $(value).closest(".js-affix-container");
        $(value).affix({
          offset: {
            top: function () {
                return (this.top = container.position().top - 50)
             },
            bottom: function () {
                return (this.bottom = document.body.scrollHeight - container.position().top - container.outerHeight())
            }
          }
        });
        $(value).affix('checkPosition');
    });
}

$(document).ready(function(){
    setTimeout(() => {
       setAffix();
        $(window).scroll();
    }, 280);
});

$( window ).resize(function() {
  setAffix();
  $(window).scroll();
});

