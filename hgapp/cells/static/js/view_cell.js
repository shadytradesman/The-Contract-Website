
$(function(){
    function handleWorldEventsClick() {
        $('#settingTab').click();
    }
    $("#js-all-world-tab").click(handleWorldEventsClick);
    const anchorIndex = window.location.href.indexOf('#');
    if(anchorIndex > -1) {
            $('#settingTab').click();
            var element = document.getElementById(window.location.href.slice(anchorIndex + 1));
            var bodyRect = document.body.getBoundingClientRect(),
                elemRect = element.getBoundingClientRect(),
                offset   = elemRect.top - bodyRect.top;
            $(element).find(".js-expandable-collapsed").click();
            window.scrollTo(0, offset-50);
    } else {
    }
});

