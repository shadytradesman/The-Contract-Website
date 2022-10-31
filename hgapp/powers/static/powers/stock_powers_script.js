/* TUTORIAL MODALS */

var cookieName = "default";

function setCookie(name,value,days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}
function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

$(document).ready(function(){
    var fullCookieName =  "stockGiftTutorial"+cookieName;
    var x = getCookie(fullCookieName);
    if (showTutorial && !x) {
        $('#mainTutorialModal').modal({});
        setCookie(fullCookieName,'True',700);
    }
});

function isElementInViewport (el) {
    if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
    }
    var rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

$(".unstyled-link").on("click", function(ev){
    setTimeout(() => {
        let target = ev.target;
        if (!isElementInViewport(target)) {
            target.scrollIntoView();
            window.scrollBy(0,-100);
        }
    }, 280);
});