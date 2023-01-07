function setAffix() {
    $('.js-affix-image').each(function( index, value ) {
        let container = $(value).closest(".js-affix-container");
        $(value).affix({
          offset: {
            top: function () {
                return (this.top = container.position().top - 50)
             },
            bottom: function () {
                return (this.bottom = document.body.scrollHeight - container.position().top - container.outerHeight() - 50)
            }
          }
        });
        $(value).affix('checkPosition');
    });
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

