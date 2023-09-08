$(document).ready(function(){
    var fullCookieName =  "exchangeTutorial"+cookieName;
    var x = getCookie(fullCookieName);
    if (showTutorial && !x) {
        $('#mainTutorialModal').modal({});
        setCookie(fullCookieName,'True',700);
    }
});
