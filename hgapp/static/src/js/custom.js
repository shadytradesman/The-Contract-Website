/* Tooltips */
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});

/* Power badge stuff */
$(document).on("click", ".power-badge a", function(e) {
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
	"Non-Sapient": "Any target that does not think or is not self-aware.",
	"Living": "Only targets that are alive.",
	"Non-Living": "Only targets that are not alive.",
	"Dead": "Only targets that were once alive.",
	"Animate": "Only targets that can move or think on their own.",
	"Inanimate": "Only targets that cannot move or think on their own.",
	"Creature": "Only targets that are living, animate, and non-sapient.",
	"Object": "Only Inanimate, non-living targets that are also free-standing, loose, or otherwise not currently a part of another structure or device.",
    "Device": "An Object that was designed or created for some purpose.",
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


