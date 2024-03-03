const interactiveTutorial = ["Need help?", {
    "I don't know what to make": ["Are you making this Gift for a specific Contractor?", {
        "Yes": ["What's the trouble?", {
            "I need ideas for flavorful Gifts": ["ps2-flavorful-gifts"],
            "My Gifts don't feel useful": ["What Status is your Contractor?", {
                "Novice (<10 Victories)": ["ps2-novice-gift-advice"],
                "Seasoned (10-25 Victories)": ["ps2-seasoned-gift-advice"],
                "Veteran (25+ Victories)": ["ps2-veteran-gift-advice"]
            }]
        }],
        "No": ["Why are you making a Gift?", {
            "Just trying out this system": ["ps2-trying-out-system"],
            "I'm making a Gift for an NPC": ["ps2-npc-gifts"]
            }]
        }],
    "I'm having trouble creating what I want": ["ps2-limitations-block"],
    "I'm curious about this Gift Builder": ["What about the Gift Builder?", {
        "How do I use it?": ["ps2-gift-rules"],
        "What is its design philosophy?": ["ps2-gift-philosophy"]
    }]
}];

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
    var fullCookieName = isStock ? "power2TutorialStock"+cookieName : "power2Tutorial"+cookieName;
    var x = getCookie(fullCookieName);
    if (showTutorial && !x) {
        $('#mainTutorialModal').modal({});
        setCookie(fullCookieName,'True',700);
    }
});


/* html character decoding */

String.prototype.decodeHTML = function() {
    var map = {
        "gt":">",
         "lt": "<"/* , … */};
    return this.replace(/&(#(?:x[0-9a-f]+|\d+)|[a-z]+);?/gi, function($0, $1) {
        if ($1[0] === "#") {
            return String.fromCharCode($1[1].toLowerCase() === "x" ? parseInt($1.substr(2), 16)  : parseInt($1.substr(1), 10));
        } else {
            return map.hasOwnProperty($1) ? map[$1] : $0;
        }
    });
};

function activateTooltips() {
    $('[data-toggle="tooltip"]').tooltip("enable");
    $('body').tooltip({
          selector: '.has-popover' // have to use class for some reason.
        });
}

function removeSpacesBeforePeriods(inputText) {
    return inputText.replaceAll(" .", ".");
}

const prefixReg = new RegExp('[\\d]+', 'gm');
// This method sets the __prefix__ values that appear in django "empty" formset forms so formsets
// can have dynamically added and subtracted entries
function setFormInputPrefixValues() {
    $(".js-data-prefix-container").each(function(){
        let prefixNum = $(this).attr("data-prefix");
        $(this).find("input").each(function() {
            let currName = $(this).attr("name");
            let renderedName = currName.replace(/__prefix__/g, prefixNum);
            renderedName = renderedName.replace(prefixReg, prefixNum);

            let currId = $(this).attr("id");
            let renderedId = currId.replace(/__prefix__/g, prefixNum);
            renderedId = renderedId.replace(prefixReg, prefixNum);

            $(this).attr("name", renderedName);
            $(this).attr("id", renderedId);
            $(this).attr("required", true);
        })
        $(this).find("label").each(function() {
            let currFor = $(this).attr("for");
            if (currFor) {
                let renderedFor = currFor.replace(/__prefix__/g, prefixNum);
                renderedFor = renderedFor.replace(/__prefix__/g, prefixNum)
                $(this).attr("for", renderedFor);
            }
        })
    })
}

function onlyUnique(value, index, self) {
    return self.indexOf(value) === index;
}

$(document).ready(activateTooltips);

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

function displayCost(cost) {
    let prefix =  cost >= 0 ? "+" : "";
    let content = prefix + cost;
    let cssClass = cost < 0 ? "css-component-gift-credit" : cost == 0 ? "" : "css-component-gift-price";
    return "<span class=\"" + cssClass +"\">" + content + "</span>";
};

function replaceSubstring(match) {
	const trimmed = match.trim();
	return ' <span class="css-keyword-with-tooltip" data-toggle="tooltip" title="' + powerKeywordDict[trimmed] + '">' + trimmed + '</span> ';
}

let powerBlob = null;
let characterBlob = null;
let powerEditBlob = null;
var unrenderedSystemText = "";

function componentToVue(component, type) {
    return {
        id: type + "-" + component.slug,
        slug: component.slug,
        icon_url: component.icon_url,
        displayName: component.name,
        summary: component.summary,
        description: component.description,
        errata: component.system_errata,
        visibility: component.system_visibility,
        type: component.type,
        giftCredit: component["gift_credit"],
        visibility: component.default_description_prompt,
        requiredStatus: component.required_status[0],
        requiredStatusLabel: component.required_status[0] === "ANY" ? false : component.required_status[1],
    }
}
const filterDisplayByVecSlug = {
    "direct": {
        "signature-item-mod": "is used on a target",
        "power": "is used on a target",
        "craftable-consumable": "are used on targets",
        "craftable-artifact": "can be used on targets",
    },
    "at-will": {
        "signature-item-mod": "can be activated to empower myself",
        "power": "temporarily empowers myself",
        "craftable-consumable": "empower their users",
        "craftable-artifact": "empower their users when activated",
    },
    "passive": {
        "signature-item-mod": "grants a passive benefit",
        "power": "is passive",
        "craftable-consumable": "??",
        "craftable-artifact": "grant a passive benefit",

    },
    "trap": {
        "signature-item-mod": "???",
        "power": "places traps",
        "craftable-consumable": "are traps",
        "craftable-artifact": "??",
    },
    "functional": {
        "signature-item-mod": "is an enhanced version of a normal object",
        "power": "??",
        "craftable-consumable": "???",
        "craftable-artifact": "are enhanced versions of normal objects",
    },
}

function vectorSlugToEffectFilter(vecSlug, modalitySlug) {
    return {
        id: "effect-filter-" + vecSlug,
        value: vecSlug,
        display: filterDisplayByVecSlug[vecSlug][modalitySlug],
    };
}

function modifierToVue(modifier, type) {
    modCounter++;
    return modifierToVueWithId(modifier, type, modCounter);
}

function modifierToVueWithId(modifier, type, idNum) {
    let domNameBase = "modifs-" + idNum;
    let idBase = "id_" + domNameBase;
    const isEnhancement = type == "enhancements";
    const colorMethod = isEnhancement ? markEnhancementText : markDrawbackText;
    return {
        id: idBase,
        idNum: idNum,
        isEnhancement: isEnhancement,
        checkboxName: domNameBase + "-is_selected",
        checkboxId: idBase + "-is_selected",
        detailsName: domNameBase + "-details",
        detailsId: idBase + "-details",
        details: "",
        hiddenFormId: 0,
        slug: modifier.slug,
        displayName: modifier.name,
        eratta: modifier.eratta,
        description: colorMethod(replaceHoverText(modifier.description)),
        detailLabel: modifier.detail_field_label === null ? false : modifier.detail_field_label,
        requiredStatusLabel: modifier.required_status[0] === "ANY" ? false : modifier.required_status[1],
        requiredStatus: modifier.required_status,
        category: modifier.category,
        categoryClass: "css-cat-" + modifier.category,
        group: modifier.group,
    }
}

function powerParamToVue(powerParam) {
    return {
        powParamId: powerParam.id,
        id: powerParam.param_id,
        name: powerBlob["parameters"][powerParam.param_id]["name"],
        eratta: powerParam.eratta,
        defaultLevel: powerParam["default_level"],
        seasonedLevel: powerParam["seasoned_threshold"],
        vetLevel: powerParam["veteran_threshold"],
        levels: powerParam.levels,
    }
}

function requiredStatusOfParam(powerParam, currentLevel) {
    for (let i = 0; i < powerParam.levels.length; i++) {
        if (powerParam.levels[i] === currentLevel) {
            if (i >= powerParam.vetLevel) {
                return ["VETERAN", "Veteran"];
            }
            if (i >= powerParam.seasonedLevel) {
                return ["SEASONED", "Seasoned"];
            }
            return null;
        }
    }
}

function giftCostOfVueParam(powerParam, currentLevel) {
    for (let i = 0; i < powerParam.levels.length; i++) {
        if (powerParam.levels[i] === currentLevel) {
            return i - powerParam.defaultLevel;
        }
    }
}

function selectedLevelOfParam(powerParam, currentLevel) {
    for (let i = 0; i < powerParam.levels.length; i++) {
        if (powerParam.levels[i] === currentLevel) {
            return i;
        }
    }
}

function systemFieldToVue(systemField, type) {
    let isRoll = type === "roll";
    let isWeapon = type === "weapon";
    const attributeChoices = isRoll ? systemField["attribute_choices"] : [];
    const abilityChoices = isRoll ? systemField["ability_choices"] : [];
    const weaponChoices = isWeapon ? systemField["weapon_choices"] : [];
    return {
        id: type + systemField.id,
        pk: systemField.id,
        marker: systemField.marker,
        replacement: systemField.replacement,
        name: systemField.name,
        eratta: systemField.eratta,
        isRoll: isRoll,
        isText: type === "text",
        isWeapon: isWeapon,
        weaponChoices: weaponChoices,
        attributeChoices: attributeChoices,
        abilityChoices: abilityChoices,
    }
}

function modifiersFromComponents(components, modifier, existing) {
    selectedModifierSlugs = components.flatMap(component => component[modifier]);
    blacklistModifierSlugs = components.flatMap(component => component["blacklist_" + modifier]);
    let allowedModifiers = selectedModifierSlugs.filter(x => !blacklistModifierSlugs.includes(x));
    let updatedModifiers = existing.filter(mod => allowedModifiers.includes(mod.slug));
    let activeModifierSlugs = existing.map(mod => mod.slug);
    let newModifiers = allowedModifiers.filter(mod => !activeModifierSlugs.includes(mod)).map(id => modifierToVue(powerBlob[modifier][id], modifier));
    updatedModifiers = updatedModifiers.concat(newModifiers);
    return sortVueModifiers(updatedModifiers);
}

function globalGroupLabelFromId(groupId) {
    return powerBlob["enhancement_group_by_pk"][groupId]["label"];
}

function sortVueModifiers(modifiers) {
    modifiers.sort((a,b) => {
        let compareNameA = a.group == null ? a.displayName : globalGroupLabelFromId(a.group) + a.displayName;
        let compareNameB = b.group == null ? b.displayName : globalGroupLabelFromId(b.group) + b.displayName;
        return compareNameA.localeCompare(compareNameB);
    });
    return modifiers;
}

function handleModifierMultiplicity(modSlug, modId, modType, existingModifiers, selectedAndActiveModifiers) {
    let returnedModifiers = existingModifiers;
    let mod = powerBlob[modType][modSlug];
    if (mod.multiplicity_allowed) {
      let numSelected = selectedAndActiveModifiers.filter(curMod => curMod.slug === modSlug).length;
      let numAvail = existingModifiers.filter(curMod => curMod["slug"] === modSlug).length;
      if (numSelected == numAvail && numAvail < 4) {
          returnedModifiers.push(modifierToVue(mod, modType));
      } else if (numAvail - numSelected > 1){
          returnedModifiers = existingModifiers.filter(mod => mod["id"] != modId);
      }
    }
    return sortVueModifiers(returnedModifiers);
}

function paramsFromComponents(components, modifier) {
    let powerParams = components.flatMap(component => component["parameters"]);
    let blacklistedParamSlugs = components.flatMap(component => component["blacklist_parameters"]);
    let allowedParams = powerParams.filter(x => !blacklistedParamSlugs.includes(x["param_id"]));
    return allowedParams.map(param => powerParamToVue(param));
}

function fieldsFromComponents(components, unrenderedSystemText) {
    textFields = components.flatMap(component => component["text_fields"])
        .filter(field => unrenderedSystemText.includes(field["marker"]))
        .map(field => systemFieldToVue(field, "text"));
    rollFields = components.flatMap(component => component["roll_fields"])
        .filter(field => unrenderedSystemText.includes(field["marker"]))
        .map(field => systemFieldToVue(field, "roll"));
    weaponFields = components.flatMap(component => component["weapon_fields"])
        .map(field => systemFieldToVue(field, "weapon"));
    return textFields.concat(rollFields.concat(weaponFields));
}

function getDisabledParameters(availParameters, activeUniqueReplacementsByMarker) {
    disabledModifiers = {};
    availParameters.forEach(modifier => {
        let blobMod = powerBlob["parameters"][modifier.id];
        blockedSubs = blobMod["substitutions"]
            .filter(sub => sub["mode"] === "UNIQUE")
            .filter(sub => sub["marker"] in activeUniqueReplacementsByMarker
                && activeUniqueReplacementsByMarker[sub["marker"]]["id"] != modifier.id);
        if (blockedSubs.length > 0) {
            if (!(modifier.id in disabledModifiers)) {
               disabledModifiers[modifier.id] = [];
            }
        }
        blockedSubs.forEach(sub => {
            let warningString = "Can't be taken with " + activeUniqueReplacementsByMarker[sub["marker"]]["name"];
            if (!disabledModifiers[modifier.id].includes(warningString)) {
                disabledModifiers[modifier.id].push(warningString);
            }
        });
    });
    return disabledModifiers;
}

function getDisabledModifiers(modType, availModifiers, selectedModifiers, activeUniqueReplacementsByMarker, allAvailModifiers) {
    // given a modType ("enhancement"), available modifiers, and selected modifiers.
    // return a mapping of disabled modifiers of that type to an array of reasons they are disabled.
    const powerBlobFieldName = modType + "s";
    const otherFieldName = modType == "enhancement" ? "drawbacks" : "enhancements";
    const allModifiers = {...powerBlob[otherFieldName], ...powerBlob[powerBlobFieldName]};
    const requiredEnhancements = "required_enhancements";
    const requiredDrawbacks = "required_drawbacks";
    unfulfilledModifiers = availModifiers
          .filter(modifier => {
              let required = powerBlob[powerBlobFieldName][modifier.slug][requiredEnhancements]
                     .concat(powerBlob[powerBlobFieldName][modifier.slug][requiredDrawbacks]);
              let secondOrderReq = required.flatMap(mod => allModifiers[mod][requiredEnhancements].concat(allModifiers[mod][requiredDrawbacks]));
              let allRequired = new Set(required.concat(secondOrderReq).filter(req => {
                return allAvailModifiers.map(mod=>mod.slug).includes(req);
              }));

              if (allRequired.length == 0) {
                  return false;
              }
              const unsatisfiedRequirements = Array.from(allRequired)
                  .filter(reqMod => !selectedModifiers.includes(reqMod));
              if (unsatisfiedRequirements.length == 0) {
                  return false;
              }
              return true;
          });
    disabledModifiers = {};
    unfulfilledModifiers.forEach(mod => {
       if (!(mod.slug in disabledModifiers)) {
           disabledModifiers[mod.slug] = [];
       }
       requiredSlugs = allModifiers[mod.slug][requiredEnhancements].concat(powerBlob[powerBlobFieldName][mod.slug][requiredDrawbacks]);
       requiredSlugs.forEach(reqSlug => {
           disabledModifiers[mod.slug].push("Requires: " + allModifiers[reqSlug]["name"]);
       });
    });
    availModifiers.forEach(modifier => {
        let blobMod = powerBlob[powerBlobFieldName][modifier.slug];
        blockedSubs = blobMod["substitutions"]
            .filter(sub => sub["mode"] === "UNIQUE")
            .filter(sub => sub["marker"] in activeUniqueReplacementsByMarker
                && activeUniqueReplacementsByMarker[sub["marker"]]["slug"] != blobMod["slug"]);
        if (blockedSubs.length > 0) {
            if (!(modifier.slug in disabledModifiers)) {
               disabledModifiers[modifier.slug] = [];
            }
        }
        blockedSubs.forEach(sub => {
            let message = "Cannot be taken with " + activeUniqueReplacementsByMarker[sub["marker"]]["name"];
            if (!disabledModifiers[modifier.slug].includes(message)) {
                disabledModifiers[modifier.slug].push(message);
            }
        });
    });
    return disabledModifiers;
}

function buildModifierDetailsMap(vueModifiers) {
    let detailsMap = {};
    vueModifiers.forEach(mod => {
        if (!(mod.slug in detailsMap)) {
            detailsMap[mod.slug] = [];
        }
        detailsMap[mod.slug].push(mod.details);
    })
    return detailsMap;
}

const htmlReplaceMap = {
    '(': '&#40;',
    ')': '&#41;',
    '[': '&#91;',
    ']': '&#93;',
    '&': '&#38;',
    '%': '&#37;',
    '|': '&#124;',
    '{': '&#123;',
    '}': '&#125;',
    '$': '&#36;',
    '+': '&#43;',
    '#': '&#35;',
    ';': '&#59;',
    '!': '&#33;',
    '*': '&#42;',
    '<': '&lt;',
    '>': '&gt;',
    '\'': '&#x27;',
    '\"': '&quot;'
}

function cleanUserInputField(userInput){
    let output = "";
    for (let i = 0; i < userInput.length; i++) {
        let char = userInput[i];
        if (char in htmlReplaceMap) {
            output += htmlReplaceMap[char];
        }
        else {
            output += char;
        }
    }
    return output;
}


function subUserInputForDollarSign(replacementText, userInput) {
    userInput = '<span class="css-system-text-user-input">' + userInput + "</span>";
    return replacementText.replaceAll("$", userInput);
}

function markRollText(rollReplacementText) {
    return '<span class="css-system-text-roll">' + rollReplacementText + "</span>";
}

function markEnhancementText(modifierReplacementText) {
    let numText = Number(modifierReplacementText);
    if (modifierReplacementText.length == 0 || Number.isInteger(numText)) {
        // don't surround integers with tags otherwise addition replacement tags break
        return modifierReplacementText;
    }
    return '<span class="css-system-text-enhancement">' + modifierReplacementText + "</span>";
}

function markDrawbackText(modifierReplacementText) {
    let numText = Number(modifierReplacementText);
    if (modifierReplacementText.length == 0 || Number.isInteger(numText)) {
        // don't surround integers with tags otherwise addition replacement tags break
        return modifierReplacementText;
    }
    return '<span class="css-system-text-drawback">' + modifierReplacementText + "</span>";
}

function addReplacementsForModifiers(replacements, selectedModifiers, detailsByModifiers, replacementFormatter) {
  let includedModSlugs = [];
  selectedModifiers
      .forEach(mod => {
          mod["substitutions"].forEach(sub => {
              const marker = sub["marker"];
              var replacement = sub["replacement"];
              let numIncludedForSlug = includedModSlugs.filter(includedSlug => includedSlug === mod["slug"] + sub["marker"]).length;
              if (replacement.includes("$")) {
                  let dollarSub = "";
                  if (mod["joining_strategy"] != "ALL") {
                      var allDetails = mod["slug"] in detailsByModifiers ? detailsByModifiers[mod["slug"]] : [""];
                      allDetails = allDetails.filter(sub => !(sub.length === 0));
                      let joiningString = allDetails.length > 2 ? ", " : " ";
                      if (allDetails.length > 1) {
                          let joiningWord = mod["joining_strategy"] === "OR" ? "or " : "and ";
                          allDetails[allDetails.length - 1] = joiningWord + allDetails[allDetails.length - 1];
                      }
                      dollarSub = allDetails.join(joiningString);
                  } else {
                      dollarSub = detailsByModifiers[mod["slug"]][numIncludedForSlug];
                  }
                  replacement = subUserInputForDollarSign(replacement, cleanUserInputField(dollarSub));
              }
              const newSub = {
                  mode: sub["mode"],
                  replacement: replacementFormatter(replacement),
              }
              includedModSlugs.push(mod["slug"] + sub["marker"]);
              if (mod["joining_strategy"] == "ALL" || numIncludedForSlug == 0) {
                  if (sub["mode"] === "UNIQUE" && numIncludedForSlug === 1) {
                      return;
                  }
                  if (marker in replacements ) {
                      replacements[marker].push(newSub);
                  } else {
                      replacements[marker] = [newSub];
                  }
              }
          })
      });
}



function collapseSubstitutions(replacements) {
    // normalizes lists of substitutions so that they follow the semantics associated with the modes:
    // EPHEMERAL, UNIQUE, and ADDITIVE.
    // EPHEMERAL subs are replaced by all other types
    // UNIQUE subs replace all other types, leaving a single substitution.
    // ADDITIVE subs can exist in any quantity.
    // return a mapping of marker string to list of replacement texts.
    var cleanedReplacements = {};
    for (var marker in replacements) {
        substitutions = replacements[marker];
        if (substitutions.length == 0) {
            throw "Empty subs for marker: " + marker;
        }
        if (substitutions.length == 1) {
            // no need to deal with modes when there's only one.
            cleanedReplacements[marker] = substitutions.map(sub => sub.replacement);
            continue;
        }
        const uniqueSubs = substitutions.filter(sub => sub["mode"] == "UNIQUE");
        if (uniqueSubs.length > 1) {
            throw "Multiple subs are unique for marker: " + marker;
        }
        if (uniqueSubs.length == 1) {
           cleanedReplacements[marker] = [uniqueSubs[0].replacement];
           continue;
        }

        const ephemeralSubs = substitutions.filter(sub => sub["mode"] == "EPHEMERAL");
        const nonEphemeralSubs = substitutions.filter(sub => sub["mode"] != "EPHEMERAL");
        if (ephemeralSubs.length > 0 && nonEphemeralSubs.length > 0) {
            cleanedReplacements[marker] = nonEphemeralSubs.map(sub => sub.replacement);
            continue;
        }
        if (ephemeralSubs.length > 1) {
            cleanedReplacements[marker] = [ephemeralSubs[0].replacement];
            continue;
        }
        cleanedReplacements[marker] = substitutions.map(sub => sub.replacement);
    }
    for (var marker in cleanedReplacements) {
        cleanedReplacements[marker] = cleanedReplacements[marker].filter(sub => sub.length > 0);
        if (cleanedReplacements[marker].length == 0) {
            cleanedReplacements[marker] = [""];
        }
    }
    return cleanedReplacements;
}

function performSystemTextReplacements(unrenderedSystem, replacementMap, usedMarkers) {
    var systemText = unrenderedSystem;
    var toReplace = findReplacementCandidate(systemText);
    var replacementCount = 0;
    while (toReplace != null) {
        usedMarkers.push.apply(usedMarkers, toReplace.markers);
        systemText = replaceInSystemText(systemText, replacementMap, toReplace);
        var toReplace = findReplacementCandidate(systemText);
        replacementCount ++;
        if (replacementCount > 1000) {
            throw "More than one thousand replacements in system text. . . infinite loop?"
        }
    }
    return removeSpacesBeforePeriods(systemText);
}

function replaceInSystemText(systemText, replacementMap, toReplace) {
    const markers = toReplace.markers;
    var replacements = null;
    for (var i = 0; i < markers.length; i++) {
        if (markers[i] in replacementMap) {
            if (replacements === null) {
                replacements = [];
            }
            replacements = replacements.concat(replacementMap[markers[i]])
        }
    }
    let replacementText = getReplacementText(replacements, toReplace);
    return systemText.slice(0, toReplace.start) + replacementText + systemText.slice(toReplace.end + 1);
}

const parenJoinString = {
    '(': ', ',
    '@': ', ',
    '[': ' ',
    '{': '</p><p>',
    '#': '',
    '!': '',
    ';': "</li><li>",
}

const parenEndByStart = {
    '(': ')',
    '@': '%',
    '[': ']',
    '{': '}',
    '#': '+',
    '!': '*',
    ';': '/',
}
function getReplacementText(replacements, toReplace) {
    if (replacements === null) {
        // no replacements exist in replacement map at all.
        if (toReplace.defaultValue) {
            return toReplace.defaultValue;
        } else {
            return "";
        }
    }
    if (toReplace.type === '#') {
        return replacements.reduce((a,b) => parseInt(a) + parseInt(b)).toString();
    }
    if (toReplace.type === '!') {
        return replacements.reduce((a,b) => parseInt(a) * parseInt(b)).toString();
    }
    replacements = replacements.filter(rep => rep.length != 0);
    if (replacements.length === 0) {
        // only zero-length replacements appeared in replacement map.
        return "";
    }
    if (toReplace.type === '{') {
        replacements[0] = "</p><p>" + replacements[0];
    }
    if (toReplace.type === ';') {
        replacements[0] = "<ul class=\"css-power-system-list\"><li>" + replacements[0];
        replacements[replacements.length -1] = replacements[replacements.length -1] + "</li></ul>"
    }
    if (replacements[0].length > 0 && toReplace.capitalize) {
        let indexToCapitalize = replacements[0].indexOf(">") + 1;
        replacements[0] = replacements[0].slice(0, indexToCapitalize) + replacements[0][indexToCapitalize].toUpperCase() + replacements[0].slice(indexToCapitalize + 1);
    }
    if (replacements.length === 1 ) {
        return replacements[0];
    }
    if (toReplace.type === '(') {
        replacements[replacements.length - 1] = "and " + replacements[replacements.length - 1];
    }
    if (toReplace.type === '@') {
        replacements[replacements.length - 1] = "or " + replacements[replacements.length - 1];
    }
    let joinString = parenJoinString[toReplace.type];
    if (['@', '('].includes(toReplace.type) && replacements.length == 2) {
        joinString = " ";
    }
    return replacements.join(joinString);
}

function findReplacementCandidate(systemText) {
    // Finds the first pair of opening parenthesis, indicating a replacement substring.
    // Proceeds to the matching closure of the parens, skipping any nested replacements
    // returns a little replacement candidate object.
    let markerStarts = ['(', '[', '{', '@', '#', ';', '!'];
    let endMarker = null;
    let parenDepth = 0;
    let start = null;
    let end = null;
    let defaultContentStartIndex = null;
    let capitalize = false;
    for (var i = 0; i < systemText.length; i++) {
        const curChar = systemText[i];
        if (i > 0 && systemText[i-1] === curChar) {
            if (markerStarts.includes(curChar)) {
                // two start markers
                if (start === null) {
                    start = i - 1;
                    markerStarts = [curChar];
                    endMarker = parenEndByStart[curChar];
                }
                parenDepth = parenDepth + 1;
                // this avoids the case where we have four+ starts in a row ala [[[[
                i++;
            } else if (endMarker != null && curChar === endMarker) {
                // two end markers
                parenDepth = parenDepth - 1;
                if (parenDepth === 0) {
                    end = i;
                    if (i + 1 < systemText.length) {
                        // if ending a joining list, check for capitalization flag that appears immediately afterwards.
                        if (systemText[i+1] == '^') {
                            capitalize = true;
                            end = i + 1; // also replace ^
                        }
                    }
                    break;
                } else {
                    // this avoids the case where we have four+ ends in a row ala ]]]]
                    i++;
                }
            }
        }
        if (start != null && defaultContentStartIndex === null && curChar === '|' && parenDepth === 1) {
            defaultContentStartIndex = i;
        }
    }

    if (start === null) {
        // no candidate found
        return null;
    }

    if (end === null) {
        throw "unmatched start symbols found at: " + start;
    }

    // do markers
    const endParenIndex = capitalize ? end - 2 : end -1 ; // capitalization flag increases length by 1
    const markerEnd = defaultContentStartIndex === null ? endParenIndex : defaultContentStartIndex;
    var markerSection = systemText.slice(start + 2, markerEnd);
    markerSection = markerSection.trim();
    const markers = markerSection.split(',');
    if (!['(', '@', '#', '!'].includes(markerStarts[0]) && markers.length > 1) {
        // only list sub markers allow multiple marker strings.
        throw "Too many marker strings for non-list sub starting at: " + start;
    }

    // default values
    var defaultValue = null;
    if (defaultContentStartIndex != null) {
        defaultValue = systemText.slice(defaultContentStartIndex + 1, endParenIndex);
        defaultValue = defaultValue.trim();
    }

    return {
        type: markerStarts[0],
        capitalize: capitalize,
        markers: markers,
        defaultValue: defaultValue,
        start: start,
        end: end
    };
}

let handler = {
  get: function(target, name) {
    return target.hasOwnProperty(name) ? target[name] : [];
  }
};

function randomFromList(list) {
    return list[Math.floor(Math.random() * list.length)];
}


let modCounter = 0; // used when creating unique ids for modifiers
const ComponentRendering = {
  delimiters: ['{', '}'],
  data() {
    return {
      expandedTab: "modalities",
      tabHeader: "Select a Gift Type",
      modalities: [],
      selectedModality: null,
      modalityEffectFilterPrompt: "",
      effects: [],
      categoriesWithEffects: [],
      selectedEffect: null,
      effectFilters: [],
      selectedEffectFilter: null,
      vectors: [],
      selectedVector: null,
      enhancements: [],
      selectedEnhancements: [],
      disabledEnhancements: {}, // map of disabled enhancements slug to reason.
      advancementEnhancements: [],
      drawbacks: [],
      selectedDrawbacks: [],
      disabledDrawbacks: {}, // map of disabled drawback slug to reason.
      advancementDrawbacks: [],
      effectImageUrls: [],
      parameters: [],
      parameterSelections: {},
      disabledParameters: {},
      systemFields: [],
      fieldTextInput: {},
      fieldRollInput: new Proxy({}, handler),
      fieldWeaponInput: {},
      unrenderedSystem: '',
      renderedSystem: '',
      unrenderedDescription: "",
      giftErrata: "",
      activeUniqueReplacementsByMarker: {},
      giftCost: 0,
      giftInfoList: [],
      giftInfoHeader: "",
      previousGiftCost: null,
      costDifference: null,
      enhancementsCost: 0,
      drawbacksCost: 0,
      giftCostTooltip: " ",
      requiredStatus: null,
      requiredStatusReason: null,
      requiredStatusSatisfied: true,
      giftName: null,
      giftDescription: null,
      giftExtendedDescription: null,
      giftTagline: "",
      giftPreviewModalFirstShow: true,
      enhancementList: "",
      drawbackList: "",
      warnings: [],
      selectedItem: "",
      hasCrafted: false,
      sigItemName: "",
      sigItemDescription: "",
      renderedVisual: "",
      breadCrumbs: [],
      currentCrumb: interactiveTutorial,
      userIsAdmin: userAdmin,
      isStock: isStock,
      currentExamplePreview: "",
      currentExampleBlob: null,
      exampleEffectDisplay: "",
      lastUsedMarkers: [],
      existingArtifactPk: null,
      existingArtifactName: null,
    }
  },
  methods: {
      clickCrumb(crumb) {
        let newBreadCrumbs = [];
        let newCrumb = true;
        for (let i = 0; i < this.breadCrumbs.length; i++) {
            if (this.breadCrumbs[i][0] == crumb[0])  {
                newCrumb = false;
                break;
            }
            newBreadCrumbs.push(this.breadCrumbs[i]);
        }
        if (newCrumb) {
            newBreadCrumbs.push(this.currentCrumb);
        }
        this.breadCrumbs = newBreadCrumbs;
        this.currentCrumb = crumb;
      },
      shouldShowTutSection(section) {
        return (this.currentCrumb.length == 1) && (this.currentCrumb[0] == section);
      },
      randomGift() {
        this.parameterSelections = {};
        this.selectedModality = randomFromList(this.modalities);
        this.changeModality();
        this.selectedEffect = randomFromList(this.effects);
        this.changeEffect();
        if (this.vectors.length > 1) {
            this.selectedVector = randomFromList(this.vectors);
        }
        this.clickVector();

        let numEnhancements = Math.floor(Math.random() * 6);
        let numDrawbacks = Math.floor(Math.random() * (numEnhancements - 1)); // drawbacks < enhancements
        if (this.giftCost+numEnhancements < 0) {
            numDrawbacks = Math.max(0, numDrawbacks -1);
        }

        this.selectedEnhancements =  [];
        this.selectedDrawbacks = [];

        for (let i = 0; i < numEnhancements; i++) {
            let availEnhancements = this.enhancements.filter(enh => !(enh.slug in this.disabledEnhancements));
            if (availEnhancements == 0) {
                numDrawbacks = Math.max(i, numDrawbacks);
                break;
            }
            let selectedEnhancement = randomFromList(availEnhancements);
            selectedEnhancement.details = selectedEnhancement.detailLabel;
            this.selectedEnhancements.push(selectedEnhancement);
            this.enhancements = handleModifierMultiplicity(selectedEnhancement.slug, selectedEnhancement.id, "enhancements", this.enhancements, this.getSelectedAndActiveEnhancements());
            this.calculateRestrictedElements();
        }

        for (let i = 0; i < numDrawbacks; i++) {
            let availDrawbacks = this.drawbacks.filter(mod => !(mod.slug in this.disabledDrawbacks));
            if (availDrawbacks == 0) {
                break;
            }
            let selectedDrawback = randomFromList(availDrawbacks);
            selectedDrawback.details = selectedDrawback.detailLabel;
            this.selectedDrawbacks.push(selectedDrawback);
            this.drawbacks = handleModifierMultiplicity(selectedDrawback.slug, selectedDrawback.id, "drawbacks", this.drawbacks, this.getSelectedAndActiveDrawbacks());
            this.calculateRestrictedElements();
        }


        this.parameters.forEach(param => {
            let def = param.defaultLevel;
            if (param.id in this.disabledParameters) {
                this.parameterSelections[param.id] = param.levels[def];
                return;
            }
            if (this.giftCost <= 0) {
                this.parameterSelections[param.id] = param.levels[def + 1];
            } else {
                let new_level = Math.floor(Math.random() * (Object.keys(param.levels).length - 1))
                let cost = new_level - def;
                if (this.giftCost + cost > 0 && this.giftCost + cost < 6) {
                    this.parameterSelections[param.id] = param.levels[new_level];
                } else {
                    this.parameterSelections[param.id] = param.levels[def];
                }
            }
            this.changeParam();
        })

        this.updateManagementForms();
        this.reRenderSystemText();
        this.updateGiftCost();
        this.updateRequiredStatus();
        this.populateWarnings();
        this.openCustomizationTab();
        $("#giftPreviewModal").modal({});
      },
      setStateForAddEffect(existingArtifactPk, existingArtifactName) {
        this.existingArtifactPk = existingArtifactPk;
        this.existingArtifactName = existingArtifactName;
        this.selectedModality = this.modalities.find(comp => comp.slug === "signature-item-mod");
        this.selectedItem = this.existingArtifactPk;
        this.giftPreviewModalFirstShow = false;
        this.changeModality();
        console.log("modality selected");
      },
      setStateForEdit(powerEditBlob) {
        this.giftName = powerEditBlob["name"].decodeHTML();
        this.giftTagline = powerEditBlob["flavor_text"];
        this.giftDescription = powerEditBlob["description"];
        this.giftExtendedDescription = powerEditBlob["extended_description"];
        this.previousGiftCost = powerEditBlob["current_cost"];
        this.hasCrafted = powerEditBlob["has_crafted"];
        let selectedModality = this.modalities.find(comp => comp.slug === powerEditBlob["modality_pk"]);
        if (!selectedModality) {
            return;
        }
        this.selectedModality = selectedModality;
        this.giftPreviewModalFirstShow = false;
        this.changeModality();
        console.log("modality selected");
        console.log("effect: " + powerEditBlob["effect_pk"]);
        if (this.selectedModality.slug === "signature-item-mod" && powerEditBlob["current_artifact"] != null) {
            this.selectedItem = powerEditBlob["current_artifact"];
        }
        let selectedEffect = this.effects.find(comp => comp.slug === powerEditBlob["effect_pk"]);
        console.log(selectedEffect);
        if (!selectedEffect) {
            return;
        }
        console.log("effect selected");
        this.selectedEffect = selectedEffect;
        this.changeEffect();
        if (this.vectors.length > 1) {
            let selectedVector = null;
            if (null === powerEditBlob["vector_pk"]) {
                selectedVector = this.vectors[0];
            } else {
                selectedVector = this.vectors.find(comp => comp.slug === powerEditBlob["vector_pk"]);
            }
            if (!selectedVector) {
                return;
            }
            this.selectedVector = selectedVector;
        }
        this.clickVector();
        console.log("Vector assigned");

        this.selectedEnhancements =  [];
        this.selectedDrawbacks = [];

        function applyEnhancement(state, mod) {
            let availEnhancements = state.enhancements.filter(enh =>
                !(enh.slug in state.disabledEnhancements)
                && !(state.selectedEnhancements.map(e => e.id).includes(enh.id)));
            let selectedEnhancement = availEnhancements.find(enh => enh.slug === mod["enhancement_slug"]);
            if (selectedEnhancement) {
                if (mod["is_advancement"]) {
                    state.advancementEnhancements.push(selectedEnhancement);
                } else {
                    if (mod["detail"] != null) {
                        selectedEnhancement.details = mod["detail"].decodeHTML();
                    }
                    state.selectedEnhancements.push(selectedEnhancement);
                    state.enhancements = handleModifierMultiplicity(selectedEnhancement.slug, selectedEnhancement.id, "enhancements", state.enhancements, state.getSelectedAndActiveEnhancements());
                    state.calculateRestrictedElements();
                    return true;
                }
            }
            return false;
        }

        function applyDrawback(state, mod) {
            let availDrawbacks = state.drawbacks.filter(drawback =>
                !(drawback.slug in state.disabledDrawbacks)
                && !(state.selectedDrawbacks.map(d => d.id).includes(drawback.id)));
            let selectedDrawback = availDrawbacks.find(drawback => drawback.slug === mod["drawback_slug"]);
            if (selectedDrawback) {
                if (mod["detail"] != null) {
                    selectedDrawback.details = mod["detail"].decodeHTML();
                }
                if (mod["is_advancement"]) {
                    state.advancementDrawbacks.push(selectedDrawback);
                    return false;
                }
                state.selectedDrawbacks.push(selectedDrawback);
                state.drawbacks = handleModifierMultiplicity(selectedDrawback.slug, selectedDrawback.id, "drawbacks", state.drawbacks, state.getSelectedAndActiveDrawbacks());
                state.calculateRestrictedElements();
                return true;
            }
            return false;
        }
        let enhancementsToApply = powerEditBlob["enhancements"];
        let drawbacksToApply = powerEditBlob["drawbacks"];
        for (let i = 0; i < 5; i++) {
            // this is a hacky way to deal with enhancement and drawback prerequisites without building a
            // dependency tree.
            enhancementsToApply = enhancementsToApply.filter(mod => !applyEnhancement(this, mod));
            drawbacksToApply = drawbacksToApply.filter(mod => !applyDrawback(this, mod));
        }

        powerEditBlob["text_fields"].forEach(editField => {
            this.systemFields.forEach(sysField => {
                if (sysField.isText && sysField.pk === editField["field_id"]) {
                    this.fieldTextInput[sysField.id] = editField["value"].decodeHTML();
                }
            });
        });

        console.log("Text fields assigned");

        powerEditBlob["weapon_fields"].forEach(editField => {
            this.systemFields.forEach(sysField => {
                if (sysField.isWeapon && sysField.pk === editField["field_id"]) {
                    this.fieldWeaponInput[sysField.id] = editField["weapon_id"];
                }
            });
        });
        console.log("Weapon fields assigned");

        powerEditBlob["roll_fields"].forEach(editField => {
            this.systemFields.forEach(sysField => {
                if (sysField.isRoll && sysField.pk === editField["field_id"]) {
                    this.fieldRollInput[sysField.id][0] = editField["roll_attribute"];
                    if (editField["roll_ability"]) {
                        this.fieldRollInput[sysField.id][1] = editField["roll_ability"];
                    }
                }
            });
        });
        console.log("roll fields assigned");

        powerEditBlob["parameters"].forEach(editParam => {
            this.parameters.forEach(param => {
                if (editParam["power_param_pk"] == param["powParamId"]) {
                    this.parameterSelections[param.id] = param["levels"][editParam["value"]];
                }
            });
        });
        console.log("parameters assigned");

        this.updateManagementForms();
        this.reRenderSystemText();
        this.updateGiftCost();
        this.updateRequiredStatus();
        this.populateWarnings();
        this.openCustomizationTab(false);
        console.log("Edit power completed");
      },
      populateErrata() {

        let errataLines = [""];
        errataLines = this.getSelectedAndActiveEnhancements.map(mod => mod["eratta"]);
        errataLines = errataLines.concat(this.getSelectedAndActiveDrawbacks.map(mod => mod["eratta"]));
        this.giftErrata = "";
      },
      scrollToContent() {
          this.$nextTick(function () {
              let yPos = document.getElementById("js-content-header").getBoundingClientRect().y -60;
              window.scrollTo(0, yPos);
          });
      },
      scrollToTop() {
          this.$nextTick(function () {
              window.scrollTo(0, 0);
          });
      },
      openModalityTab(userClick) {
          this.expandedTab = "modalities";
          this.tabHeader = "Select a Gift Type";
          this.scrollToTop();
          if (userClick) {
            window.location.hash = '#modalities';
          }
      },
      openEffectsTab(userClick) {
          this.expandedTab = "effects";
          this.tabHeader = "Select an Effect";
          this.scrollToTop();
          if (userClick) {
          }
          window.location.hash = '#effects';
      },
      openCustomizationTab(userClick) {
          this.expandedTab = "customize";
          this.tabHeader = "Customize System";
          this.scrollToTop();
          if (userClick) {
            window.location.hash = '#customization';
          }
          this.$nextTick(function () {
            if (this.giftPreviewModalFirstShow && window.innerWidth <= 770) {
                $('#giftPreviewModal').modal({});
            }
            setFormInputPrefixValues();
          });
      },
      clickModalityTab() {
          if (this.existingArtifactPk) {
            return
          }
          if (this.expandedTab === "modalities" && this.selectedModality) {
              if (this.selectedEffect === null) {
                  this.openEffectsTab(true);
                  this.scrollToTop();
              } else {
                  this.openCustomizationTab(true);
                  this.scrollToTop();
              }
          } else {
              this.openModalityTab(true);
              this.scrollToTop();
          }
      },
      clickEffectsTab() {
          if (this.expandedTab === "effects" && this.selectedEffect) {
              this.openCustomizationTab(true);
              this.scrollToTop();
          } else if (this.selectedModality) {
              this.openEffectsTab(true);
              this.scrollToTop();
          }
      },
      clickCustomizationTab() {
          if (this.selectedModality && this.selectedEffect) {
              this.openCustomizationTab(true);
              this.scrollToTop();
          }
      },
      clickModality(modality) {
          if (this.selectedModality && modality.target.getAttribute("id") === this.selectedModality.id) {
              if (this.selectedEffect === null) {
                  this.openEffectsTab(true);
              } else {
                  this.openCustomizationTab(true);
              }
          }
      },
      clickEffect(effect) {
          if (this.selectedEffect && effect.target.getAttribute("id") === this.selectedEffect.id) {
              this.openCustomizationTab(true);
          }
      },
      clickEffectExample(example) {
        let baseSlug = example.target.attributes["value"].value;
        let url = '/gift/ajax/example/effect/' + baseSlug + '/';
        this.currentExamplePreview = "";
        this.currentExampleBlob = null;
        this.exampleEffectDisplay = example.target.attributes["display"].value;
        $.ajax({
            type: 'GET',
            url: url,
            success: function (response) {
                console.log("success");
                mountedApp.currentExamplePreview = response["preview"];
                mountedApp.currentExampleBlob = response["edit_blob"];
            },
            error: function (response) {
                console.log(response);
                mountedApp.currentExamplePreview = "<h3 class=\"text-center\">Error Fetching Example</h3>"
            }
        })
        $("#giftExampleModal").modal({});
      },
      customizeExampleGift() {
        this.setStateForEdit(this.currentExampleBlob);
        $("#giftExampleModal").modal('hide');
      },
      updateEffectCategoryDisplay() {
          let categories = powerBlob["component_categories"]
          let categoriesWithEffects= []
          categories.forEach(category => {
              let catEffects = this.effects.filter(effect => category.components.includes(effect.slug))
                  .filter(effect => this.satisfiesEffectFilter(effect.slug));
              if (catEffects.length > 0) {
                  categoriesWithEffects.push({
                      "name": category.name,
                      "description": category.description,
                      "color": category.color,
                      "containerClass": category.container_class,
                      "effects": catEffects,
                  })
              }
          });
          this.categoriesWithEffects = categoriesWithEffects;
      },
      changeModality(modality) {
          const allowed_effects = powerBlob["effects_by_modality"][this.selectedModality.slug];
          this.effects = Object.values(powerBlob.effects)
              .filter(comp => allowed_effects.includes(comp.slug))
              .map(comp => componentToVue(comp, "effect"));

          this.updateEffectFilters();
          this.updateEffectCategoryDisplay();

          let shouldOpenEffectsTab = false;
          if (this.selectedEffect === null || !allowed_effects.includes(this.selectedEffect.slug)) {
              this.selectedEffect = null;
              shouldOpenEffectsTab = true;
          }
          this.updateAvailableVectors();

          this.componentClick();
          if (shouldOpenEffectsTab) {
              this.openEffectsTab(true);
          } else {
              this.openCustomizationTab(true);
          }
          this.scrollToTop();
      },
      changeEffectFilter() {
          this.updateEffectCategoryDisplay();
      },
      clickEffectFilter(filter) {
          if (this.selectedEffectFilter && filter.target.getAttribute("id") === this.selectedEffectFilter.id) {
              this.setEffectFilterToAll();
              this.updateEffectCategoryDisplay();
          }
      },
      getCostForEffect(effectSlug, effectGiftCredit) {
        // A cost is only displayed for an Effect if there is only one Vector for the Effect and the combined cost is non-zero.
        const allowedVectors = this.getAvailableVectorsForEffectAndModality(effectSlug, this.selectedModality.slug)
            .map(comp => componentToVue(powerBlob.vectors[comp], "vector"));
        let costs = allowedVectors.map(vector => {
            let cost = this.additionalCostOfComponents(effectSlug, vector["slug"], this.selectedModality.slug);
            return cost - vector["giftCredit"] - effectGiftCredit;
        });
        if (costs.length > 1 ) {
            // will display cost on style selection.
            return null;
        }
        costs = costs.filter(cost => cost != 0);
        if (costs.length == 1) {
            return " (Gift Cost: " + displayCost(costs[0]) + ")";
        }
        return null;
      },
      costDisplay(cost) {
        return displayCost(cost)
      },
      getCostForVector(vectorSlug) {
        // the displayed cost for a vector is the combined cost of the effect and vector together.
        let credit = powerBlob.vectors[vectorSlug]["gift_credit"] + this.selectedEffect.giftCredit;
        let cost = this.additionalCostOfComponents(this.selectedEffect["slug"], vectorSlug, this.selectedModality.slug) - credit;
        if (cost != 0) {
            return "(Gift Cost: " + displayCost(cost) + ")";
        }
        return null;
      },
      giftCostOfVueParam(param) {
        return giftCostOfVueParam(param, this.parameterSelections[param.id]);
      },
      selectedLevelOfParam(param) {
        return selectedLevelOfParam(param, this.parameterSelections[param.id]);
      },
      updateManagementForms() {
          let modHiddenFormCounter = 0;
          this.enhancements.forEach(enh => {
            enh.hiddenFormId = modHiddenFormCounter;
            modHiddenFormCounter ++;});
          this.drawbacks.forEach(drawb => {
            drawb.hiddenFormId = modHiddenFormCounter;
            modHiddenFormCounter ++;});
          $('#id_modifiers-TOTAL_FORMS').attr('value', this.enhancements.length + this.drawbacks.length + 1);
          $('#id_parameters-TOTAL_FORMS').attr('value', this.parameters.length);
          $('#id_sys_field_text-TOTAL_FORMS').attr('value', this.systemFields.filter(field => field.isText).length);
          $('#id_sys_field_weapon-TOTAL_FORMS').attr('value', this.systemFields.filter(field => field.isWeapon).length);
          $('#id_sys_field_roll-TOTAL_FORMS').attr('value', this.systemFields.filter(field => field.isRoll).length);
          this.$nextTick(function () {
                setFormInputPrefixValues();
          });
      },
      updateEffectFilters() {
          let allAvailableVectors = Array.from(new Set(this.effects
              .flatMap(effect => this.getAvailableVectorsForEffectAndModality(effect.slug, this.selectedModality.slug))));
          let newEffectFilters = [];
          if (this.selectedModality.slug === "craftable-artifact") {
            this.modalityEffectFilterPrompt = "I craft Artifacts that";
          }
          if (this.selectedModality.slug === "craftable-consumable") {
            this.modalityEffectFilterPrompt = "I craft Consumables that";
          }
          if (this.selectedModality.slug === "power") {
            this.modalityEffectFilterPrompt = "My Power";
          }
          if (this.selectedModality.slug === "signature-item-mod") {
            this.modalityEffectFilterPrompt = "My Legendary Artifact";
          }

          this.effectFilters = newEffectFilters.concat(allAvailableVectors.map(vecSlug => vectorSlugToEffectFilter(vecSlug, this.selectedModality.slug)));
          this.setEffectFilterToAll();
      },
      setEffectFilterToAll() {
          let allFilter = {
              id: "effect-filter-ALL",
              value: "ALL",
              display: "",
          };
          this.selectedEffectFilter = allFilter;
      },
      satisfiesEffectFilter(effectSlug) {
          if (this.selectedEffectFilter.value === "ALL") {
              return true;
          }
          let allAvailableVectors = this.getAvailableVectorsForEffectAndModality(effectSlug, this.selectedModality.slug);
          return allAvailableVectors.includes(this.selectedEffectFilter.value);
      },
      groupLabelFromId(groupId) {
        return globalGroupLabelFromId(groupId);
      },
      changeEffect(effect) {
          this.updateAvailableVectors();
          if (this.selectedEffectFilter.value != "ALL") {
              this.selectedVector = this.vectors.find(comp => comp.slug === this.selectedEffectFilter.value);
          }
          this.componentClick();
          this.openCustomizationTab(true);
          this.scrollToTop();
      },
      updateAvailableVectors() {
          if (this.selectedEffect === null) {
              this.vectors = [];
              this.selectedVector = null;
              return;
          }
          const allowedVectors = this.getAvailableVectorsForEffectAndModality(this.selectedEffect.slug, this.selectedModality.slug);
          let unsortedVectors = Object.values(powerBlob.vectors)
              .filter(comp => allowedVectors.includes(comp.slug))
              .map(comp => componentToVue(comp, "vector"));
          this.vectors = sortVueModifiers(unsortedVectors);
          if (!this.selectedVector || !allowedVectors.includes(this.selectedVector.slug)) {
              this.selectedVector = this.vectors[0];
          }
      },
      getAvailableVectorsForEffectAndModality(effectSlug, modalitySlug) {
          const effectVectors = powerBlob["vectors_by_effect"][effectSlug];
          const modalityVectors = powerBlob["vectors_by_modality"][modalitySlug];
          return effectVectors.filter(x => modalityVectors.includes(x));
      },
      clickVector(vector) {
          this.componentClick();
      },
      changeParam() {
          this.calculateRestrictedElements();
          this.reRenderSystemText();
          this.updateGiftCost();
          this.updateRequiredStatus();
          this.populateWarnings();
      },
      componentClick() {
		if (this.selectedVector && this.selectedModality && this.selectedEffect) {
			this.populatePowerForm();
        }
      },
      getSelectedComponents() {
           return [
               powerBlob.modalities[this.selectedModality.slug],
               powerBlob.effects[this.selectedEffect.slug],
               powerBlob.vectors[this.selectedVector.slug]
           ]
      },
      populatePowerForm() {
        components = this.getSelectedComponents();
        const modality = components[0];
        const effect = components[1];
        const vector = components[2];
        console.log("updating power form with the following modality, effect and vector");
        console.log(modality);
        console.log(effect);
        console.log(vector);
        this.unrenderedSystem = "<p>" + vector["system_text"] + "</p><p>" + effect["system_text"] + "</p>";
        this.unrenderedDescription = modality["system_text"];
        this.drawbacks = modifiersFromComponents(components, "drawbacks", this.drawbacks);
        this.enhancements = modifiersFromComponents(components, "enhancements", this.enhancements);
        this.parameters = paramsFromComponents(components);
        this.parameters.forEach(param => {
            this.parameterSelections[param.id] = param.levels[param["defaultLevel"]];
        });
        this.systemFields = fieldsFromComponents(components, this.unrenderedSystem + this.unrenderedDescription);
        this.systemFields.forEach(field => {
            if (field.isWeapon) {
                this.fieldWeaponInput[field.id] = field.weaponChoices[0][0];
            } else if (field.isRoll) {
                let defaultChoices = [field.attributeChoices[0]];
                if (field.abilityChoices.length > 0) {
                    defaultChoices.push(field.abilityChoices[0]);
                }
                this.fieldRollInput[field.id] = defaultChoices;
            } else {
                this.fieldTextInput[field.id] = "________";
            }
        });

        this.calculateRestrictedElements();
        this.updateManagementForms();
        this.reRenderSystemText();
        this.updateGiftCost();
        this.updateRequiredStatus();
        this.populateWarnings();
        this.$nextTick(function () {
            activateTooltips();
            setFormInputPrefixValues();
        });
      },
      updateGiftCost() {
          let componentsCost = 1;
          this.getSelectedComponents().forEach(comp => {
              componentsCost = componentsCost - comp["gift_credit"];
          });
          componentsCost = componentsCost + this.additionalCostOfComponents(this.selectedEffect["slug"], this.selectedVector.slug, this.selectedModality.slug)

          this.enhancementsCost = this.getSelectedAndActiveEnhancements().length
          this.drawbacksCost = - this.getSelectedAndActiveDrawbacks().length;

          let parametersCost = 0;
          this.parameters.forEach(param => {
              parametersCost = parametersCost + this.giftCostOfVueParam(param);
          });
            // displayCost
          let toolTip = "Type, Effect, and Style: " + displayCost(componentsCost);
          toolTip = toolTip + (this.enhancementsCost != 0 ? "<br>Enhancements: " + displayCost(this.enhancementsCost) : "");
          toolTip = toolTip + (this.drawbacksCost != 0 ? "<br>Drawbacks: " + displayCost(this.drawbacksCost) : "");
          toolTip = toolTip + (parametersCost != 0 ? "<br>Parameters: " + displayCost(parametersCost) : "");
          this.giftCostTooltip = toolTip;
          this.giftCost = componentsCost + this.enhancementsCost + this.drawbacksCost + parametersCost;
          this.$nextTick(function () {
              activateTooltips();
              setFormInputPrefixValues();
          });
          if (null != this.previousGiftCost) {
            let costDiff = this.giftCost - this.previousGiftCost;
            let prefix = costDiff >= 0 ? "+ " : " ";
            this.costDifference = prefix + costDiff;
          }
          this.updateGiftText();
      },
      updateGiftText() {
        if (null != characterBlob) {
            this.giftInfoList = [];
            this.giftInfoHeader = "";
            let spentRewards = null != powerEditBlob ? powerEditBlob["spent_rewards"] : [];
            let numInvested = spentRewards.length;
            let unpaidCost = this.giftCost - numInvested;
            let availRewards = characterBlob["avail_rewards"];
            if (unpaidCost > 0) {
                if (availRewards.length > 0) {
                    this.giftInfoHeader = "Saving will spend the following Rewards";
                    this.giftInfoList = availRewards.slice(0, unpaidCost);
                }
            }
            if (unpaidCost == 0) {
                this.giftInfoHeader = "Saving will not affect " + characterBlob["name"] + "'s Rewards";
                this.giftInfoList = [];
            }
            if (unpaidCost < 0) {
                if (numInvested > 0) {
                    this.giftInfoHeader = "Saving will refund the following Rewards"
                    this.giftInfoList = spentRewards.slice(0, -unpaidCost);
                }
            }
        }
      },
      mergeStatuses(currentStatus, requiredStatus, reason) {
            if (null == requiredStatus || ["ANY", "NEWBIE"].includes(requiredStatus[0])) {
                return currentStatus;
            }
            if (requiredStatus[0] === "VETERAN") {
                this.requiredStatusReason = reason;
                return requiredStatus;
            }
            if (requiredStatus[0] === "SEASONED" && (null === currentStatus || currentStatus[0] === "ANY" || currentStatus[0] === "NOVICE")) {
                this.requiredStatusReason = reason;
                return requiredStatus;
            }
            if (requiredStatus[0] === "NOVICE" && (null === currentStatus || currentStatus[0] === "ANY")) {
                this.requiredStatusReason = reason;
                return requiredStatus;
            }
            return currentStatus;
      },
      updateRequiredStatus() {
        let requiredStatus = null;
        this.requiredStatusSatisfied = true;
        this.requiredStatusReason = null;
        let selectedEnhancements = this.getSelectedAndActiveEnhancements();
        let countByGroups = {};
        let active_groups = this.enhancements.filter(enh => null != enh.group)
            .map(enh => powerBlob["enhancement_group_by_pk"][enh.group]).filter(onlyUnique);

        selectedEnhancements.forEach(enh => {
            requiredStatus = this.mergeStatuses(requiredStatus, enh.requiredStatus, enh.displayName);
        });
        this.getSelectedComponents().forEach(comp => {
            requiredStatus = this.mergeStatuses(requiredStatus, comp["required_status"], comp.name);
        });
        this.parameters.forEach(param => {
            requiredStatus = this.mergeStatuses(requiredStatus, requiredStatusOfParam(param, this.parameterSelections[param.id]), param.name);
        });
        active_groups.forEach(group => {
            const numSelectedOfGroup = selectedEnhancements.filter(enh => enh["group"] === group.pk).length;
            if (group.veteran_threshold && numSelectedOfGroup >= group.veteran_threshold) {
                requiredStatus = this.mergeStatuses(requiredStatus, ["VETERAN", "Veteran"], group.label);
            }
            if (group.seasoned_threshold && numSelectedOfGroup >= group.seasoned_threshold) {
                requiredStatus = this.mergeStatuses(requiredStatus, ["SEASONED", "Seasoned"], group.label);
            }
        });
        if (null != characterBlob && null != requiredStatus) {
            let char_status = characterBlob["status"];
            if (requiredStatus[0] == "SEASONED" && !['SEASONED', 'PROFESSIONAL', 'VETERAN'].includes(char_status)) {
                this.requiredStatusSatisfied = false;
            }
            if (requiredStatus[0] == "NOVICE" && !['NOVICE', 'SEASONED', 'PROFESSIONAL', 'VETERAN'].includes(char_status)) {
                this.requiredStatusSatisfied = false;
            }
            if (requiredStatus[0] == "VETERAN" && char_status != "VETERAN") {
                this.requiredStatusSatisfied = false;
            }
        }

        this.requiredStatus = requiredStatus == null || requiredStatus[0] == "ANY" ? null : requiredStatus[1];

      },
      additionalCostOfComponents(effectSlug, vectorSlug, modalitySlug) {
          let cost =0;
          powerBlob["effect_vector_gift_credit"].filter(cred => cred["vector"] === vectorSlug
                && cred["effect"] === effectSlug
                && ((cred["modality"] === null) || (cred["modality"] == modalitySlug)))
                .forEach(comp => {
                    cost= cost - comp["credit"];
                });
          return cost;
      },
      populateWarnings() {
        // NOTE: This method must be called after gift cost is calculated.
        let new_warnings = [];

        // gift cost warning
        if (this.giftCost <= 0) {
            new_warnings.push("Gifts must cost a minimum of one Gift Credit");
        }

        // Group min required enhancements warnings
        let selectedEnhancements = this.getSelectedAndActiveEnhancements();
        let active_groups = this.enhancements.filter(enh => null != enh.group)
            .map(enh => powerBlob["enhancement_group_by_pk"][enh.group]).filter(onlyUnique);
        active_groups.forEach(group => {
            const numSelectedOfGroup = selectedEnhancements.filter(enh => enh["group"] === group.pk).length;
            if (null != group.min_required && numSelectedOfGroup < group.min_required) {
                new_warnings.push("This Gift requires at least " + group.min_required + " " + group.label + " Enhancement");
            }
        });

        if (null != characterBlob) {
            let spentRewards = null != powerEditBlob ? powerEditBlob["spent_rewards"] : [];
            let numInvested = spentRewards.length;
            let unpaidCost = this.giftCost - numInvested;
            if (unpaidCost > characterBlob["avail_rewards"].length) {
                new_warnings.push("You do not have sufficient Rewards available to purchase this Gift.");
            }
        }

        this.warnings = new_warnings;
      },
      calculateRestrictedElements() {
          this.populateUniqueReplacementsMap();
          this.disabledEnhancements = {};
          this.disabledDrawbacks = {};
          let selectedAndActiveSlugs = this.getSelectedAndActiveEnhancements().concat(this.getSelectedAndActiveDrawbacks()).map(mod => mod.slug);
          let allAvailModifiers = this.enhancements.concat(this.drawbacks);
          this.disabledEnhancements = getDisabledModifiers("enhancement", this.enhancements, selectedAndActiveSlugs, this.activeUniqueReplacementsByMarker, allAvailModifiers);
          this.selectedEnhancements = this.selectedEnhancements.filter(mod => !(mod.slug in this.disabledEnhancements));
          this.disabledDrawbacks = getDisabledModifiers("drawback", this.drawbacks, selectedAndActiveSlugs, this.activeUniqueReplacementsByMarker, allAvailModifiers);
          this.selectedDrawbacks = this.selectedDrawbacks.filter(mod => !(mod.slug in this.disabledDrawbacks));
          this.disabledParameters = {};
          this.disabledParameters = getDisabledParameters(this.parameters, this.activeUniqueReplacementsByMarker);
      },
      populateUniqueReplacementsMap() {
          // modifiers that have "unique" field replacements "block" modifiers that uniquely replace the same thing.
          this.activeUniqueReplacementsByMarker = {};
          this.getSelectedAndActiveEnhancements().concat(this.getSelectedAndActiveDrawbacks()).map(mod => mod["slug"]).forEach(mod => {
              let modifier = mod in powerBlob["enhancements"] ? powerBlob["enhancements"][mod] : powerBlob["drawbacks"][mod];
              modifier["substitutions"].filter(sub => sub["mode"] === "UNIQUE").forEach(sub => {
                 this.activeUniqueReplacementsByMarker[sub["marker"]] = modifier;
             });
          });
          this.parameters.filter(param => param.levels[param["defaultLevel"]] != this.parameterSelections[param["id"]]).forEach(param => {
              powerBlob["parameters"][param.id]["substitutions"].filter(sub => sub["mode"] === "UNIQUE").forEach(sub => {
                  this.activeUniqueReplacementsByMarker[sub["marker"]] = param;
              });
          });
      },
      clickEnhancement(modifier) {
          console.log("clicked Enhancement");
          let modSlug = modifier.target._value.slug;
          this.enhancements = handleModifierMultiplicity(modSlug, modifier.target._value.id, "enhancements", this.enhancements, this.getSelectedAndActiveEnhancements());
          this.calculateRestrictedElements();
          this.updateManagementForms();
          this.reRenderSystemText();
          this.updateGiftCost();
          this.updateRequiredStatus();
          this.populateWarnings();
      },
      clickDrawback(modifier) {
          console.log("clicked Drawback");
          let modSlug = modifier.target._value.slug;
          this.drawbacks = handleModifierMultiplicity(modSlug, modifier.target._value.id, "drawbacks", this.drawbacks, this.getSelectedAndActiveDrawbacks());
          this.calculateRestrictedElements();
          this.updateManagementForms();
          this.reRenderSystemText();
          this.updateGiftCost();
          this.updateRequiredStatus();
          this.populateWarnings();
      },
      reRenderSystemText() {
          const replacementMap = this.buildReplacementMap();
          let usedMarkers = [];
          this.renderedDescription = performSystemTextReplacements(this.unrenderedDescription, replacementMap, usedMarkers);
          let partiallyRenderedSystem = performSystemTextReplacements(this.unrenderedSystem, replacementMap, usedMarkers);
          this.renderedSystem = replaceHoverText(partiallyRenderedSystem);
          this.giftErrata = performSystemTextReplacements(";;gift-errata//", replacementMap, usedMarkers);
          if (this.selectedEffect && this.selectedEffect.visibility) {
            this.renderedVisual = performSystemTextReplacements(this.selectedEffect.visibility, replacementMap, usedMarkers);
          } else {
            this.renderedVisual = "";
          }
          this.$nextTick(function () {
              activateTooltips();
              $("#js-preview-gift-button").addClass("flashing");
              setTimeout(function(){
		        $("#js-preview-gift-button").removeClass("flashing");
	          }, 100);
          });
          this.lastUsedMarkers = usedMarkers;
          this.updateModifierList();
      },
      updateModifierList() {
        let enhancementNames =  this.getSelectedAndActiveEnhancements().map(mod => mod.displayName);
        let val = "";
        if (enhancementNames.length > 0) {
            val = val + "<b>Enhancements</b>:<br>" + enhancementNames.join("<br>");
        }
        this.enhancementList = val;

        let drawbackNames =  this.getSelectedAndActiveDrawbacks().map(mod => mod.displayName);
        val = "";
        if (drawbackNames.length > 0) {
            val = val + "<b>Drawbacks</b>:<br>" + drawbackNames.join("<br>");
        }
        this.drawbackList = val;
      },
      getSelectedAndActiveEnhancements() {
          return this.enhancements.filter(enh => this.selectedEnhancements.map(enh => enh.id).includes(enh["id"]));
      },
      getSelectedAndActiveDrawbacks() {
          return this.drawbacks.filter(drawb => this.selectedDrawbacks.map(mod => mod.id).includes(drawb["id"]));
      },
      getRequiredStatusEnhancements(status) {
        if (status === 'ANY') {
            return this.enhancements.filter(enh => ['ANY', 'NEWBIE'].includes(enh.requiredStatus[0]))
        } else {
            return this.enhancements.filter(enh => enh.requiredStatus[0] == status);
        }
      },
      getRequiredStatusDrawbacks(status) {
        return this.drawbacks.filter(drb => drb.requiredStatus[0] == status);
      },
      buildReplacementMap() {
          // replacement marker to list of substitution objects
          replacements = {}
          replacements["gift-name"] = [{
            mode: "UNIQUE",
            replacement: this.giftName === null ? "Artifact" : this.giftName
          }];
          addReplacementsForModifiers(replacements,
                                      this.getSelectedAndActiveEnhancements().map(mod => mod["slug"]).map(mod => powerBlob["enhancements"][mod]),
                                      buildModifierDetailsMap(this.getSelectedAndActiveEnhancements()),
                                      markEnhancementText);
          addReplacementsForModifiers(replacements,
                                      this.getSelectedAndActiveDrawbacks().map(mod => mod["slug"]).map(mod => powerBlob["drawbacks"][mod]),
                                      buildModifierDetailsMap(this.getSelectedAndActiveDrawbacks()),
                                      markDrawbackText);
          this.addReplacementsForComponents(replacements);
          this.addReplacementsForParameters(replacements);
          this.addReplacementsForFields(replacements);

          console.log("Raw replacement map");
          console.log(replacements);

          replacements = collapseSubstitutions(replacements);
          console.log("replacement map with collapsed subs");
          console.log(replacements);
          return replacements;
      },
      addReplacementsForComponents(replacements) {
          components = this.getSelectedComponents();
          components.forEach(component => {
              component["substitutions"].forEach(sub => {
                  const marker = sub["marker"];
                  var replacement = sub["replacement"];
                  const newSub = {
                      mode: sub["mode"],
                      replacement: replacement,
                  }
                  if (marker in replacements ) {
                      replacements[marker].push(newSub);
                  } else {
                      replacements[marker] = [newSub];
                  }
              })
          });
      },
      addReplacementsForParameters(replacements) {
          this.parameters.filter(param => !(param.id in this.disabledParameters)).forEach(parameter => {
              const selection = this.parameterSelections[parameter.id];
              if (selection === undefined) {
                return;
              }
              let blobParam = powerBlob["parameters"][parameter.id];
              if (blobParam["render_lvl_zero"] || selectedLevelOfParam(parameter, selection) > 0) {
                blobParam["substitutions"].forEach(sub => {
                    const marker = sub["marker"];
                    var replacement = sub["replacement"];
                    if (replacement.includes("$")) {
                        replacement = replacement.replaceAll("$", selection);
                    }
                    const newSub = {
                        mode: sub["mode"],
                        replacement: replacement,
                    }
                    if (marker in replacements ) {
                        replacements[marker].push(newSub);
                    } else {
                        replacements[marker] = [newSub];
                    }
                });
                replacements[parameter.id + "-param-level"] = [{
                    mode: "ADDITIVE",
                    replacement: selectedLevelOfParam(parameter, selection).toString(),
                }];
              }
          });
      },
      isSignatureItem() {
        return this.selectedModality && this.selectedModality.slug === "signature-item-mod";
      },
      isCraftedArtifact() {
        return this.selectedModality && this.selectedModality.slug === "craftable-artifact";
      },
      isCraftedConsumable() {
        return this.selectedModality && this.selectedModality.slug === "craftable-consumable";
      },
      addReplacementsForFields(replacements) {
          this.systemFields.forEach(field => {
              if (field.isWeapon) {
                weaponReplacements = powerBlob["weapon_replacements_by_pk"][this.fieldWeaponInput[field.id]];
                weaponReplacements.forEach(repl => {
                    replacements[repl.marker] = [{
                        replacement: repl.replacement,
                        mode: repl.mode,
                    }]
                })
              } else {
                if (!(field.marker in replacements)) {
                    replacements[field.marker] = [];
                }
                let sub = "";
                if (field.isText) {
                    sub = cleanUserInputField(this.fieldTextInput[field.id]);
                }
                if (field.isRoll) {
                    const choices = this.fieldRollInput[field.id];
                    sub = choices[0][1];
                    if (choices.length > 1) {
                        sub = sub + " + " + choices[1][1];
                    }
                }
                let replacement = field.replacement;
                if (replacement.includes("$")) {
                    replacement = field.isRoll ? replacement.replaceAll("$", sub) : subUserInputForDollarSign(replacement, sub);
                }
                if (field.isRoll) {
                    replacement = markRollText(replacement);
                }
                replacements[field.marker].push({
                    replacement: replacement,
                    mode: "ADDITIVE",
                });
              }
          })
      }
  }
}
const app = Vue.createApp(ComponentRendering);
const mountedApp = app.mount('#vue-app');

$(function() {
    fetch(powerBlobUrl)
        .then(response => response.json())
        .then(data => {
            powerBlob = data;
            if ((document.getElementById('characterBlob').textContent.length > 2)) {
                characterBlob = JSON.parse(JSON.parse(document.getElementById('characterBlob').textContent));
            }
            mountedApp.modalities = Object.values(powerBlob.modalities).map(comp => componentToVue(comp, "mod"));
            mountedApp.effectImageUrls = Object.values(powerBlob.effects).map(comp => comp.icon_url);
            if ((document.getElementById('powerEditBlob').textContent.length > 2)) {
                powerEditBlob = JSON.parse(JSON.parse(document.getElementById('powerEditBlob').textContent));
                mountedApp.setStateForEdit(powerEditBlob);
            }
            mountedApp.$nextTick(function () {
              activateTooltips();
            });
            if (existingArtifactPk != null) {
                mountedApp.setStateForAddEffect(existingArtifactPk, existingArtifactName);
            }
            $('#giftPreviewModal').on('hidden.bs.modal', function (e) {
              mountedApp.giftPreviewModalFirstShow = false;
            });
            $('#vue-app').show();
            $('#loading-spinner').hide();
            if (!(document.getElementById('powerEditBlob').textContent.length > 2) && (existingArtifactPk === null)) {
                window.location.hash = '#modalities';
            }
        });
    window.onpopstate = function() {
        switch(location.hash) {
            case '#customization':
                mountedApp.openCustomizationTab(true);
                break
            case '#effects':
                mountedApp.openEffectsTab(true);
                break
            case '#modalities':
                mountedApp.openModalityTab(true);
                break
            default:
                history.back();
        }
    }
});
