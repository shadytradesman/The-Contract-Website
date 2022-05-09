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

const keywordHighlights = [
    // Targeting
	{
	    "regex": regexFromKeyword("Sapient"),
	    "tooltip": "An intelligent being that thinks and is self-aware.",
	},
	{
	    "regex": regexFromKeyword("Non-Sapient"),
	    "tooltip": "Anything that does not think or is not self-aware.",
	},
	{
	    "regex": regexFromKeyword("Living"),
	    "tooltip": "Beings that are alive.",
	},
	{
	    "regex": regexFromKeyword("Non-Living"),
	    "tooltip": "Anything that is not alive.",
	},
	{
	    "regex": regexFromKeyword("Dead"),
	    "tooltip": "Anything that were once alive but no longer is.",
	},
	{
	    "regex": regexFromKeyword("Animate"),
	    "tooltip": "Any being that can move or think on its own.",
	},
	{
	    "regex": regexFromKeyword("Construct"),
	    "tooltip": "Any being that is sapient and non-living.",
	},
	{
	    "regex": regexFromKeyword("Inanimate"),
	    "tooltip": "Anything that cannot move or think on its own.",
	},
	{
	    "regex": regexFromKeyword("Creature"),
	    "tooltip": "Anything that is living, animate, and non-sapient.",
	},
	{
	    "regex": regexFromKeyword("Object"),
	    "tooltip": "Anything that is non-living, inanimate, and is not a critical component of a larger structure or device (i.e. a spark plug is not an object unless it is removed from the engine).",
	},
    {
        "regex": regexFromKeyword("Device"),
        "tooltip": "Any Object that was designed or created for some purpose.",
    },
    {
        "regex": regexFromKeyword("Plant"),
        "tooltip": "Any non-sapient living thing that cannot act.",
    },
    {
        "regex": regexFromKeyword("Computer"),
        "tooltip": "A non-living device that takes input, processes data, and produces output. Generally electric.",
    },
    {
        "regex": regexFromKeyword("Vehicle"),
        "tooltip": "A device designed to move from one place to another while carrying cargo or passengers.",
    },
    {
        "regex": regexFromKeyword("Alien"),
        "tooltip": "Something that is not of this world or is unknown to this world. For example, in a modern setting, anything that does not exist in real life, such as magic.",
    },
    {
        "regex": regexFromKeyword("Non-Alien"),
        "tooltip": "Something that is of this world or known by this world. For example, in a modern setting, anything that exists in real life.",
    },

    // Other
    {
        "regex": regexFromKeyword("Concentration"),
        "tooltip": "While concentrating you can only take Free Actions and a single Quick Action per Round. Disrupting events (like taking damage) cause the effect to end, and you cannot Concentrate again until the end of the next Round."
    },
    {
        "regex": regexFromKeyword("Resist"),
        "tooltip": "The target of this Effect must consent to its use or be unconscious, bound, or incapacitated."
    },
    {
        "regex": regexFromKeyword("Resisted"),
        "tooltip": "The target of this Effect must consent to its use or be unconscious, bound, or incapacitated."
    },
    {
        "regex": new RegExp('[\\s](\\+[\\d]+ dice)([.,\\s])', 'gm'),
        "tooltip": "Multiple bonuses to the same dice pool do not stack. Instead, the highest bonus is used."
    }
];

$(document).ready(function(){
    updateHoverText();
});

function updateHoverText() {
    $('.js-render-power-keywords').each(function(){
        $(this).html(replaceHoverText($(this).html()));
    });
    $('[data-toggle="tooltip"]').tooltip();
}

function regexFromKeyword(text) {
    return new RegExp('[\\s](' + text + "s?)([.,\\s])", 'gm');
}

function replaceHoverText(text) {
    let modifiedText = text;
    keywordHighlights.forEach(keyword => {
        let replacementString = ' <span class="css-keyword-with-tooltip" data-toggle="tooltip" title="' + keyword.tooltip + '">$1</span>$2 '
        modifiedText = modifiedText.replaceAll(keyword.regex, replacementString);
    });
    return modifiedText;
}
