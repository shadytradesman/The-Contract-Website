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
    const $window = $(window);
    $('.css-art-front-punk').followTo(textHeight);

    const $contractors = $('#contractors');
    const contractorsEnd =  document.body.scrollHeight - $contractors.position().top - $contractors.outerHeight(true);
    $('#css-art-front-time').affix({
      offset: {
        top: $contractors.position().top -50,
        bottom:  contractorsEnd +50 ,
      }
    })

    const $games = $("#games");
    const gamesEnd =  document.body.scrollHeight - $games.position().top - $games.outerHeight(true);
    $('#css-art-front-doors').affix({
      offset: {
        top: $games.position().top -50,
        bottom:  gamesEnd +50,
      }
    })

    const $dice = $("#dice");
    const diceEnd =  document.body.scrollHeight - $dice.position().top - $dice.outerHeight(true);
    $('#css-art-front-bamboo').affix({
      offset: {
        top: $dice.position().top -50,
        bottom:  diceEnd +50,
      }
    })

    const $website = $("#website");
    const websiteEnd =  document.body.scrollHeight - $website.position().top - $website.outerHeight(true);
    $('#css-art-front-music').affix({
      offset: {
        top: $website.position().top -50,
      }
    })

    const startedHeight = textHeight -  $('#get-started-wrapper').outerHeight(true) -130;
    $('#get-started').affix({
      offset: {
        top: startedHeight,
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

function updateAffix() {
    $(window).scroll();
    setTimeout(() => {  $(window).scroll(); }, 700);
    setTimeout(() => {$('#css-art-front-time').affix('checkPosition'); }, 700);
    setTimeout(() => {$('#css-art-front-doors').affix('checkPosition'); }, 700);
    setTimeout(() => {$('#css-art-front-bamboo').affix('checkPosition'); }, 700);
    setTimeout(() => {$('#css-art-front-music').affix('checkPosition'); }, 700);
}

$("a").click(function() {
    updateAffix();
});

$(".power-badge").click(function() {
    updateAffix();
});