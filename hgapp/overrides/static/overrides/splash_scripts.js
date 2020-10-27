function setAffix() {
    const $window = $(window);
    const $home = $('#home');
    const homeEnd =  document.body.scrollHeight - $home.position().top - $home.outerHeight(true);

    $('.css-art-front-punk').affix({
      offset: {
        top: -50,
        bottom:  homeEnd + 50,
      }
    })

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
    var topBamboo;
    var bottomBamboo;
    const diceEnd =  document.body.scrollHeight - $dice.position().top - $dice.outerHeight(true);
    topBamboo = $dice.position().top -50;
    bottomBamboo = diceEnd +50,
    $('#css-art-front-bamboo').affix({
      offset: {
        top: topBamboo,
        bottom: bottomBamboo,
      }
    })


    const $website = $("#website");
    const websiteEnd =  document.body.scrollHeight - $website.position().top - $website.outerHeight(true);
    $('#css-art-front-music').affix({
      offset: {
        top: $website.position().top -50,
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
