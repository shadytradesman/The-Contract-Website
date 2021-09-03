function setAffix() {
    const $window = $(window);
//    const $home = $('#format-punk');
//    const homeEnd =  document.body.scrollHeight - $home.position().top - $home.outerHeight(true);
//
//    $('#css-art-front-punk').affix({
//      offset: {
//        top: -50,
//        bottom:  homeEnd + 50,
//      }
//    })

    const $contractors = $('#format-punk');
    console.log("outer height: " + $contractors.outerHeight(true));
    const contractorsEnd =  document.body.scrollHeight - $contractors.position().top - $contractors.outerHeight(true);
    $('#css-art-front-punk-sm').affix({
      offset: {
        top: $contractors.position().top -50,
        bottom:  contractorsEnd +50 ,
      }
    })

    const $games = $("#format-music");
    const gamesEnd =  document.body.scrollHeight - $games.position().top - $games.outerHeight(true);
    $('#css-art-front-music-sm').affix({
      offset: {
        top: $games.position().top -50,
        bottom:  gamesEnd +50,
      }
    })
//
//    const $dice = $("#dice");
//    var topBamboo;
//    var bottomBamboo;
//    const diceEnd =  document.body.scrollHeight - $dice.position().top - $dice.outerHeight(true);
//    topBamboo = $dice.position().top -50;
//    bottomBamboo = diceEnd +50,
//    $('#css-art-front-bamboo').affix({
//      offset: {
//        top: topBamboo,
//        bottom: bottomBamboo,
//      }
//    })
//
//
//    const $website = $("#website");
//    const websiteEnd =  document.body.scrollHeight - $website.position().top - $website.outerHeight(true);
//    $('#css-art-front-music').affix({
//      offset: {
//        top: $website.position().top -50,
//      }
//    })
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


/*
* HEALTH TUTORIAL CODE
*
*/
$(document).ready(function(){
    $("#id_injury-severity").val(4);
    $("#id_injury-description").val("Bradley leg bite");
});

$(".injury-form-tutorial").submit(function (e) {
    e.preventDefault();
    var delUrl = $(this).attr("data-delete-injury-url");
    var serializedData = $(this).serializeArray();
    $("#injury-form-tutorial").trigger('reset');
    $("#id_description").focus();

//    delUrl = delUrl.replace(/injuryIdJs/g, JSON.parse(response["id"]));
    var tmplMarkup = $('#injury-template').html();
    var compiledTmpl = tmplMarkup.replace(/__description__/g, serializedData[2].value);
    var compiledTmpl = compiledTmpl.replace(/__delUrl__/g, delUrl);
    var compiledTmpl = compiledTmpl.replace(/__severity__/g, serializedData[1].value);
    $("#js-injury-container-tutorial").append(
        compiledTmpl
    )
    $("#id_injury-severity").val(1);
    $("#id_injury-description").val("");
    updateHealthDisplay();
})

// delete injury
$("#js-injury-container-tutorial").on("submit",".js-delete-injury-form-tutorial", function (e) {
    e.preventDefault();
    var injuryForm = $(this);
    injuryForm.parent().parent().remove();
    updateHealthDisplay();
})

