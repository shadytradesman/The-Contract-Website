/* Tooltips */
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});

/* Consumable action menus */
function resetPopoverContents() {
    $('.js-popover-button').each(function(){
        let content = $(this).parent().nextAll(".js-popover-content").first().html()
        $(this).popover({
            "content": content,
            "html": true,
            "sanitize": false
        });
    })
}
$(resetPopoverContents());

$('.js-popover-button').on('inserted.bs.popover', function () {
    let remQuantity = $(this).attr("data-rem-quantity");
    $(this).parent().find("span[class^='js-consumable-minus-quantity']").text(remQuantity);
})

$(document).on("click", ".js-popover-button", function(e) {
    e.stopPropagation();
    $('.js-popover-button').filter((i, p) => {
        return $(p).attr("data-title") != $(e.target).attr("data-title");
        }).popover('hide');
    $(e.target).popover('toggle');
});
$(document).on("click", ".js-popover-button >span", function(e) {
    e.stopPropagation();
    $('.js-popover-button').filter((i, p) => {
        return $(p).attr("data-title") != $(e.target).parent().attr("data-title");
        }).popover('hide');
    $(e.target).parent().popover('toggle');
});

/* Power badge stuff */
$(document).on("click", ".power-badge a", function(e) {
   e.stopPropagation();
});

$(document).on("click", ".power-badge .btn", function(e) {
   e.stopPropagation();
});

$(document).on("click", '.power-badge [data-toggle="tooltip"]', function(e) {
   e.stopPropagation();
});

/* Expandables */
$(function(){
    const collapsedClass = "js-expandable-collapsed";

    function handleExpandClick() {        // define event handler
        var $this = $(this);
        if ($this.hasClass(collapsedClass)){
            $this.removeClass(collapsedClass);
        } else {
            $this.addClass(collapsedClass);
        }
    }
    $(".expandable-outer").click(handleExpandClick);
    $(".expandable-outer a").click(function(event){
      event.stopPropagation();
    });
});

/* Power Keywords */

const powerKeywordDict = {
    // Targeting
	"Sapient": "An intelligent being that thinks and is self-aware.",
	"Non-Sapient": "Anything that does not think or is not self-aware.",
	"Living": "Beings that are alive.",
	"Non-Living": "Anything that is not alive.",
	"Dead": "Anything that were once alive but no longer is.",
	"Animate": "Any being that can move or think on its own.",
	"Construct": "Any being that is sapient and non-living.",
	"Inanimate": "Anything that cannot move or think on its own.",
	"Creature": "Anything that is living, animate, and non-sapient.",
	"Object": "Anything that is non-living, inanimate, and also free-standing, loose, or otherwise not currently a part of another structure or device.",
    "Device": "Any Object that was designed or created for some purpose.",
    "Plant": "Any non-sapient living thing that cannot act.",
    "Computer": "A non-living device that takes input, processes data, and produces output. Generally electric.",
    "Vehicle": "A device designed to move from one place to another while carrying cargo or passengers.",
    "Alien": "Something that is not of this world or not common to this world.",

    // Other
    "Concentration": "While concentrating you can only take Free Actions and a single Quick Action per Round. Disrupting events (like taking damage) cause the effect to end."
};

$(document).ready(function(){
    updateHoverText();
});

function updateHoverText() {
    $('.js-render-power-keywords').each(function(){
        for(var key in powerKeywordDict) {
            $(this).html($(this).html().replaceAll(' ' + key, replaceSubstring));
        }
    });
    $('[data-toggle="tooltip"]').tooltip();
}

function replaceSubstring(match) {
	const trimmed = match.trim();
	return ' <span class="css-keyword-with-tooltip" data-toggle="tooltip" title="' + powerKeywordDict[trimmed] + '">' + trimmed + '</span>';
}


