$(".js-tab-nav").click(function(){
    const tabId = "#js-tab-" + $(this).attr("aria-controls");
    console.log(tabId);
    console.log($(tabId).get(0));
    $(tabId).tab('show');
});