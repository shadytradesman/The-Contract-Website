function setAffix() {
    const $window = $(window);

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
}

$(document).ready(function(){
    setAffix();
    $(window).scroll();
});

$( window ).resize(function() {
  setAffix();
  $(window).scroll();
});

/* Start playing highlight current step */
$(document).ready(function() {
    var first = true;
    $(".css-start-play-section").each(function(){
        if($(this).children('[class*="in"]').length==1 && first){
            $(this).addClass("css-start-play-active");
            first = false;
            return;
        }
    })
})

function updateAffix() {
    setTimeout(() => {  $(window).scroll(); }, 700);
    setTimeout(() => {$('#format-punk').affix('checkPosition'); }, 700);
    setTimeout(() => {$('#format-music').affix('checkPosition'); }, 700);
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

