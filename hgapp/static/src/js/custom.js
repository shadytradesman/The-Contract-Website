/* Tooltips */
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});

/* Disable on submit */
$(document).on("submit", ".js-disable-on-submit", function(e) {
    $(e.target).find(":submit").prop('disabled', true);
});

/* notification collapse */
let navCollapsed = true;
$(document).on("click", "#js-notif-nav-button", function(e) {
    let navPopdown = $('#js-notification-popdown');
    if (navCollapsed === true) {
        navPopdown.show();
        navCollapsed = false;
        $("#js-notif-nav-button").removeClass("css-unread-notifs-icon");
        $(".css-notif-alert").hide();
    } else {
        navPopdown.hide();
        navCollapsed = true;
    }
});

window.addEventListener('click', function(e){
    if (document.getElementById('js-notif-nav-element')) {
        if (!document.getElementById('js-notif-nav-element').contains(e.target)){
            let navPopdown = $('#js-notification-popdown');
            navPopdown.hide();
            navCollapsed = true;
        }
    }
});

$(document).on('click', '.js-notification-link', function (e) {
  e.stopPropagation();
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
	    "tooltip": "Anything that is non-living, inanimate, and also free-standing, loose, or otherwise not currently a part of another structure or device.",
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
    {
        "regex": regexFromKeyword("non-Alien"),
        "tooltip": "Something that is of this world or known by this world. For example, in a modern setting, anything that exists in real life.",
    },

    // Other
    {
        "regex": regexFromKeyword("Concentration"),
        "tooltip": "While concentrating you can only take Free Actions, a single Quick Action, and move 10 feet per Round. Disrupting events (like taking damage) cause the effect to end, and you cannot Concentrate again until the end of the next Round."
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


/* Navbar guide search */



// This Trie implementation was ripped from https://gist.github.com/tpae/72e1c54471e88b689f85ad2b3940a8f0
// The author has offered it for free but has not attached an official license.
// Please contact the owner of this repository / website if you

// Trie.js - super simple JS implementation
// https://en.wikipedia.org/wiki/Trie

// -----------------------------------------

// we start with the TrieNode
function TrieNode(key) {
  // the "key" value will be the character in sequence
  this.key = key;

  // we keep a reference to parent
  this.parent = null;

  // we have hash of children
  this.children = {};

  // check to see if the node is at the end
  this.end = false;
}

// iterates through the parents to get the word.
// time complexity: O(k), k = word length
TrieNode.prototype.getWord = function() {
  var output = [];
  var node = this;

  while (node !== null) {
    output.unshift(node.key);
    node = node.parent;
  }

  return output.join('');
};

// -----------------------------------------

// we implement Trie with just a simple root with null value.
function Trie() {
  this.root = new TrieNode(null);
}

// inserts a word into the trie.
// time complexity: O(k), k = word length
Trie.prototype.insert = function(word) {
  var node = this.root; // we start at the root 😬

  // for every character in the word
  for(var i = 0; i < word.length; i++) {
    // check to see if character node exists in children.
    if (!node.children[word[i]]) {
      // if it doesn't exist, we then create it.
      node.children[word[i]] = new TrieNode(word[i]);

      // we also assign the parent to the child node.
      node.children[word[i]].parent = node;
    }

    // proceed to the next depth in the trie.
    node = node.children[word[i]];

    // finally, we check to see if it's the last word.
    if (i == word.length-1) {
      // if it is, we set the end flag to true.
      node.end = true;
    }
  }
};

// check if it contains a whole word.
// time complexity: O(k), k = word length
Trie.prototype.contains = function(word) {
  var node = this.root;

  // for every character in the word
  for(var i = 0; i < word.length; i++) {
    // check to see if character node exists in children.
    if (node.children[word[i]]) {
      // if it exists, proceed to the next depth of the trie.
      node = node.children[word[i]];
    } else {
      // doesn't exist, return false since it's not a valid word.
      return false;
    }
  }

  // we finished going through all the words, but is it a whole word?
  return node.end;
};

// returns every word with given prefix
// time complexity: O(p + n), p = prefix length, n = number of child paths
Trie.prototype.find = function(prefix) {
  var node = this.root;
  var output = [];

  // for every character in the prefix
  for(var i = 0; i < prefix.length; i++) {
    // make sure prefix actually has words
    if (node.children[prefix[i]]) {
      node = node.children[prefix[i]];
    } else {
      // there's none. just return it.
      return output;
    }
  }

  // recursively find all words in the node
  findAllWords(node, output);

  return output;
};

// recursive function to find all words in the given node.
function findAllWords(node, arr) {
  // base case, if node is at a word, push to output
  if (node.end) {
    arr.unshift(node.getWord());
  }

  // iterate through each children, call recursive findAllWords
  for (var child in node.children) {
    findAllWords(node.children[child], arr);
  }
}

var trie = new Trie();
let guidebookSectionByTag = {};
if (document.getElementById('guidebookSearchBlob')) {
    guidebookSectionByTag = JSON.parse(JSON.parse(document.getElementById('guidebookSearchBlob').textContent));
}

$(function(){
    for (const [key, value] of Object.entries(guidebookSectionByTag)) {
        trie.insert(key.toLowerCase());
    }
});

const guidebookSearchBar = {
  delimiters: ['{', '}'],
  data() {
    return {
      articlesHit: [],
      searchBarValue: "",
    }
  },
  methods: {
      onSearch() {
        this.articlesHit = [];
        let tagHits = trie.find(this.searchBarValue.toLowerCase());
        let hitSlugs = new Set();
        for (let i = 0; i < tagHits.length; i++) {
            let articles = guidebookSectionByTag[tagHits[i]];
            for (let j = 0; j < articles.length; j++) {
                if (!hitSlugs.has(articles[j]["url"])) {
                    this.articlesHit.push(articles[j]);
                    hitSlugs.add(articles[j]["url"]);
                }
            }
        }
        this.articlesHit = this.articlesHit.sort((a,b) => a.title.length - b.title.length);
      }
  }
}

const app = Vue.createApp(guidebookSearchBar);
const mountedApp = app.mount('#js-guide-toc-nav');

const guidebookSearchBar2 = {
  delimiters: ['{', '}'],
  data() {
    return {
      articlesHit: [],
      searchBarValue: "",
    }
  },
  methods: {
      onSearch() {
        this.articlesHit = [];
        let tagHits = trie.find(this.searchBarValue.toLowerCase());
        let hitSlugs = new Set();
        for (let i = 0; i < tagHits.length; i++) {
            let articles = guidebookSectionByTag[tagHits[i]];
            for (let j = 0; j < articles.length; j++) {
                if (!hitSlugs.has(articles[j]["url"])) {
                    this.articlesHit.push(articles[j]);
                    hitSlugs.add(articles[j]["url"]);
                }
            }
        }
        this.articlesHit = this.articlesHit.sort((a,b) => a.title.length - b.title.length);
      }
  }
}

const app2 = Vue.createApp(guidebookSearchBar2);
const mountedApp2 = app2.mount('#js-guide-sidebar');

/* Archetype Generator */

let usedArchetypes = new Set();

$(function(){

    function randomFromListInner(items) {
        var selected = items[Math.floor(Math.random()*items.length)];
        if (selected instanceof Array) {
            return randomFromListInner(selected);
        }
        return selected;
    }

    // anti birthday problem wrapper function
    function randomFromList(items) {
        for (let i = 0; i < 15; i++) {
            let selected = randomFromListInner(items);
            if (!usedArchetypes.has(selected)) {
                usedArchetypes.add(selected);
                return selected;
            }
        }
        usedArchetypes.clear();
        return randomFromList(items);
    }

    if (document.getElementById('professions')) {
        const professions = JSON.parse(document.getElementById('professions').textContent);
        const archetypes = JSON.parse(document.getElementById('archetypes').textContent);
        const personalityTraits = JSON.parse(document.getElementById('personalityTraits').textContent);
        const paradigms = JSON.parse(document.getElementById('paradigms').textContent);
        const ambitions = JSON.parse(document.getElementById('ambitions').textContent);

        function randomConcept() {
            var extra = false;
            var output = "";
            if (Math.random() < 0.4) {
                output = output + " " + randomFromList(personalityTraits);
                extra = true;
            }
            if (Math.random() < 0.35) {
                output = output + " " + randomFromList(archetypes);
            } else {
                output = output + " " + randomFromList(professions);
            }
            if (Math.random() < 0.5 || !extra) {
                output = output + " " + randomFromList(paradigms);
            }
            let out = output.trim().toLowerCase();
            if (document.getElementById('js-concept')) {
                $("#js-concept").text(out);
                var el = document.getElementById('js-concept');
                el.style.animation = 'none';
                el.offsetHeight; /* trigger reflow */
                el.style.animation = null;
            }
        }

        function randomArchetype() {
            var output = "";
            if (Math.random() < 0.6) {
                output = randomFromList(personalityTraits);
            }
            if (Math.random() < 0.35) {
                output = output + " " + randomFromList(archetypes);
            } else {
                output = output + " " + randomFromList(professions);
            }
            let out = output.trim().toLowerCase();
            if (document.getElementById('id_concept_summary')) {
                $("#id_concept_summary").val(out);
            }
        }

        function randomParadigm() {
            var extra = false;
            let output = randomFromList(paradigms);
            let out = output.trim().toLowerCase();
            if (document.getElementById('id_paradigm')) {
                $("#id_paradigm").val(out);
            }
        }

        function randomAmbition() {
            var output = randomFromList(ambitions);
            $("#id_ambition").val(output.trim());
        }

        if (document.getElementById('js-random-archetype-button')) {
            document.getElementById("js-random-archetype-button").addEventListener("click", randomArchetype);
            document.getElementById("js-random-paradigm-button").addEventListener("click", randomParadigm);
            document.getElementById("js-random-ambition-button").addEventListener("click", randomAmbition);
        }
        if (document.getElementById('js-concept')) {
            window.setInterval(randomConcept, 2400);
        }
    }
});


/* TABLE STYLING */
$(document).ready(function()
{
    $("tr:odd").addClass("css-even-row");
});

$(".js-image-expand-link").click(function () {
    let element = $(this);
    if (element.attr("data-expanded") === "true") {
        let url = element.attr("data-thumb-url");
        let parent = element.parent();
        element.children().remove();
        element.append('<img class="css-thumbnail-image" src="' + url + '" />');
        element.attr("data-expanded", "false");
    } else {
        let url = element.attr("data-image-url");
        let parent = element.parent();
        element.children().remove();
        element.append('<img class="css-expanded-image" src="' + url + '" />');
        element.attr("data-expanded", "true");
    }
})
