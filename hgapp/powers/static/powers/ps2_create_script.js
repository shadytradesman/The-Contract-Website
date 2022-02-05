function activateTooltips() {
    $('[data-toggle="tooltip"]').tooltip("enable");
    $('body').tooltip({
          selector: '.has-popover'
        });
}

$(document).ready(activateTooltips);

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
        $(this).html(replaceHoverText($(this).html()));
    });
}

function replaceHoverText(text) {
    let modifiedText = text;
    for(var key in powerKeywordDict) {
        let reg = new RegExp('[\\s]' + key + "[.,\\ss]", 'gm');
        modifiedText = modifiedText.replaceAll(reg, replaceSubstring);
    }
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

const powerBlob = JSON.parse(JSON.parse(document.getElementById('powerBlob').textContent));
console.log(powerBlob);
var unrenderedSystemText = "";

function componentToVue(component, type) {
    return {
        id: type + "-" + component.slug,
        slug: component.slug,
        displayName: component.name,
        summary: component.summary,
        description: component.description,
        type: component.type,
        giftCredit: component["gift_credit"],
        visibility: component.default_description_prompt,
    }
}
const filterDisplayByVecSlug = {
    "direct": "Targeted",
    "at-will": "Self-targeting",
    "passive": "Passive",
    "trap": "Trap",
    "functional": "Extraordinary Object",
}
function vectorSlugToEffectFilter(vecSlug) {
    return {
        id: "effect-filter-" + vecSlug,
        value: vecSlug,
        display: filterDisplayByVecSlug[vecSlug],
    };
}

function modifierToVue(modifier, type) {
    return modifierToVue(modifier, type, 0);
}

function modifierToVue(modifier, type, idNum = 0) {
    return {
        id: modifier.slug + "$" + idNum + "-" + type,
        details: "",
        slug: modifier.slug,
        displayName: modifier.name,
        eratta: modifier.eratta,
        description: modifier.description,
        detailLabel: modifier.detail_field_label === null ? false : modifier.detail_field_label,
        requiredStatusLabel: modifier.required_status[0] === "ANY" ? false : modifier.required_status[1],
    }
}

function slugFromVueModifierId(vueModifierId) {
    return vueModifierId.slice(0, vueModifierId.indexOf("$"));
}

function powerParamToVue(powerParam) {
    return {
        id: powerParam.param_id,
        name: powerBlob["parameters"][powerParam.param_id]["name"],
        eratta: powerParam.eratta,
        defaultLevel: powerParam["default_level"],
        seasonedLevel: powerParam["seasoned_threshold"],
        vetLevel: powerParam["veteran_threshold"],
        levels: powerParam.levels,
    }
}

function giftCostOfVueParam(powerParam, currentLevel) {
    for (let i = 0; i < powerParam.levels.length; i++) {
        if (powerParam.levels[i] === currentLevel) {
            return i - powerParam.defaultLevel;
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

function sortVueModifiers(modifiers) {
    modifiers.sort((a,b) => a.displayName.localeCompare(b.displayName));
    return modifiers;
}

function handleModifierMultiplicity(modSlug, modId, modType, existingModifiers, selectedAndActiveModifiers) {
    let returnedModifiers = existingModifiers;
    let mod = powerBlob[modType][modSlug];
    if (mod.multiplicity_allowed) {
      let numSelected = selectedAndActiveModifiers.filter(curMod => curMod.slug === modSlug).length;
      let numAvail = existingModifiers.filter(curMod => curMod["slug"] === modSlug).length;
      if (numSelected == numAvail && numAvail < 4) {
          modCounter++;
          returnedModifiers.push(modifierToVue(mod, modType, modCounter));
      } else if (numAvail - numSelected > 1){
          returnedModifiers = existingModifiers.filter(mod => mod["id"] != modId);
      }
    }
    return sortVueModifiers(returnedModifiers);
}

function paramsFromComponents(components, modifier) {
    powerParams = components.flatMap(component => component["parameters"]);
    return powerParams.map(param => powerParamToVue(param));
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

function getDisabledModifiers(modType, availModifiers, selectedModifiers, activeUniqueReplacementsByMarker) {
    // given a modType ("enhancement"), available modifiers, and selected modifiers.
    // return a mapping of disabled modifiers of that type to an array of reasons they are disabled.
    const powerBlobFieldName = modType + "s";
    const requiredFieldName = "required_" + modType + "s";
    unfulfilledModifiers = availModifiers
          .filter(modifier => {
              const required = powerBlob[powerBlobFieldName][modifier.slug][requiredFieldName];
              if (required.length == 0) {
                  return false;
              }
              const unsatisfiedRequirements = required
                  .filter(reqEnh => !selectedModifiers.includes(reqEnh));
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
       requiredSlugs = powerBlob[powerBlobFieldName][mod.slug][requiredFieldName];
       requiredSlugs.forEach(reqSlug => {
           disabledModifiers[mod.slug].push("Requires: " + powerBlob[powerBlobFieldName][reqSlug]["name"]);
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
        blockedSubs.forEach(sub => disabledModifiers[modifier.slug]
            .push("Cannot be taken with " + activeUniqueReplacementsByMarker[sub["marker"]]["name"]));
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

function subUserInputForDollarSign(replacementText, userInput) {
    userInput = '<span class="css-system-text-user-input">' + userInput + "</span>";
    return replacementText.replace("$", userInput);
}

function markRollText(rollReplacementText) {
    return '<span class="css-system-text-roll">' + rollReplacementText + "</span>";
}

function addReplacementsForModifiers(replacements, selectedModifiers, detailsByModifiers) {
  let includedModSlugs = [];
  selectedModifiers
      .forEach(mod => {
          mod["substitutions"].forEach(sub => {
              const marker = sub["marker"];
              var replacement = sub["replacement"];
              let numIncludedForSlug = includedModSlugs.filter(includedSlug => includedSlug === mod["slug"] + sub["marker"]).length;
              if (replacement.includes("$")) {
                  let substitution = "";
                  if (mod["joining_strategy"] != "ALL") {
                      var subStrings = mod["slug"] in detailsByModifiers ? detailsByModifiers[mod["slug"]] : [""];
                      subStrings = subStrings.filter(sub => !(sub.length === 0)).map(uncleanedString => {
                          let subString = uncleanedString;
                          subString = subString.replace("((", "(");
                          subString = subString.replace("[[", "[");
                          subString = subString.replace("{{", "{");
                          subString = subString.replace("))", ")");
                          subString = subString.replace("]]", "]");
                          subString = subString.replace("}}", "}");
                          return subString;
                      })
                      let joiningString = subStrings.length > 2 ? ", " : " ";
                      if (subStrings.length > 1) {
                          let joiningWord = mod["joining_strategy"] === "OR" ? "or " : "and ";
                          subStrings[subStrings.length - 1] = joiningWord + subStrings[subStrings.length - 1];
                      }
                      substitution = subStrings.join(joiningString);
                  } else {
                      substitution = detailsByModifiers[mod["slug"]][numIncludedForSlug];
                  }
                  replacement = subUserInputForDollarSign(replacement, substitution);
              }
              const newSub = {
                  mode: sub["mode"],
                  replacement: replacement,
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



const parenJoinString = {
    '(': ', ',
    '@': ', ',
    '[': ' ',
    '{': '<br><br>',
    '+': '',
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

function performSystemTextReplacements(unrenderedSystem, replacementMap) {
    var systemText = unrenderedSystem;
    var toReplace = findReplacementCandidate(systemText);
    var replacementCount = 0;
    while (toReplace != null) {
        systemText = replaceInSystemText(systemText, replacementMap, toReplace);
        var toReplace = findReplacementCandidate(systemText);
        replacementCount ++;
        if (replacementCount > 1000) {
            throw "More than one thousand replacements in system text. . . infinite loop?"
        }
    }
    return systemText;
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
    replacements = replacements.filter(rep => rep.length != 0);
    if (replacements.length === 0) {
        // only zero-length replacements appeared in replacement map.
        return "";
    }
    if (toReplace.type === '{') {
        replacements[0] = "<br><br>" + replacements[0];
    }
    if (replacements[0].length > 0 && toReplace.capitalize) {
        replacements[0] = replacements[0][0].toUpperCase() + replacements[0].slice(1);
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

const parenEndByStart = {
    '(': ')',
    '@': '%',
    '[': ']',
    '{': '}',
    '#': '+',
}
function findReplacementCandidate(systemText) {
    // Finds the first pair of opening parenthesis, indicating a replacement substring.
    // Proceeds to the matching closure of the parens, skipping any nested replacements
    // returns a little replacement candidate object.
    let markerStarts = ['(', '[', '{', '@', '#'];
    let endMarker = null;
    let parenDepth = 0;
    let parenType = null;
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
                    if (['(', '@'].includes(markerStarts[0]) && i + 1 < systemText.length) {
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
    if (!['(', '@', '#'].includes(markerStarts[0]) && markers.length > 1) {
        // only list sub markers allow multiple marker strings.
        throw "Too many marker strings for non-list sub starting at: " + start;
    }

    // default values
    var defaultValue = null;
    if (defaultContentStartIndex != null) {
        defaultValue = systemText.slice(defaultContentStartIndex + 1, end - 1);
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


let modCounter = 1; // used when creating unique ids for modifiers
const ComponentRendering = {
  delimiters: ['{', '}'],
  data() {
    return {
      expandedTab: "modalities",
      tabHeader: "Select a Gift Type",
      modalities: [],
      selectedModality: null,
      effects: [],
      categoriesWithEffects: [],
      selectedEffect: null,
      effectFilters: [],
      selectedEffectFilter: "",
      vectors: [],
      selectedVector: "",
      enhancements: [],
      selectedEnhancements: [],
      disabledEnhancements: {}, // map of disabled enhancements slug to reason.
      drawbacks: [],
      selectedDrawbacks: [],
      disabledDrawbacks: {}, // map of disabled drawback slug to reason.
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
      renderedSystem: "",
      activeUniqueReplacementsByMarker: {},
      giftCost: 0,
      giftCostTooltip: " ",
      giftName: null,
      giftDescription: null,
      giftTagline: "",
      giftPreviewModalFirstShow: true,
    }
  },
  methods: {
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
      openModalityTab() {
          this.expandedTab = "modalities";
          this.tabHeader = "Select a Gift Type";
      },
      openEffectsTab() {
          this.expandedTab = "effects";
          this.tabHeader = "Select an Effect";
      },
      openCustomizationTab() {
          this.expandedTab = "customize";
          this.tabHeader = "Customize System";
          this.$nextTick(function () {
            if (this.giftPreviewModalFirstShow && window.innerWidth <= 770) {
                $('#giftPreviewModal').modal({});
            }
          });
      },
      clickModalityTab() {
          if (this.expandedTab === "modalities" && this.selectedModality) {
              if (this.selectedEffect === null) {
                  this.openEffectsTab();
                  this.scrollToTop();
              } else {
                  this.openCustomizationTab();
                  this.scrollToTop();
              }
          } else {
              this.openModalityTab();
              this.scrollToTop();
          }
      },
      clickEffectsTab() {
          if (this.expandedTab === "effects" && this.selectedEffect) {
              this.openCustomizationTab();
              this.scrollToTop();
          } else if (this.selectedModality) {
              this.openEffectsTab();
              this.scrollToTop();
          }
      },
      clickCustomizationTab() {
          if (this.selectedModality && this.selectedEffect) {
              this.openCustomizationTab();
              this.scrollToTop();
          }
      },
      clickModality(modality) {
          if (this.selectedModality && modality.target.getAttribute("id") === this.selectedModality.id) {
              if (this.selectedEffect === null) {
                  this.openEffectsTab();
              } else {
                  this.openCustomizationTab();
              }
          }
      },
      clickEffect(effect) {
          if (this.selectedEffect && effect.target.getAttribute("id") === this.selectedEffect.id) {
              this.openCustomizationTab();
          }
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
              this.openEffectsTab();
          } else {
              this.openCustomizationTab();
          }
          this.scrollToTop();
      },
      changeEffectFilter() {
          this.updateEffectCategoryDisplay();
      },
      getCostForEffect(effectSlug, effectGiftCredit) {
        // A cost is only displayed for an Effect if there is only one Vector for the Effect and the combined cost is non-zero.
        const allowedVectors = this.getAvailableVectorsForEffectAndModality(effectSlug, this.selectedModality.slug)
            .map(comp => componentToVue(powerBlob.vectors[comp], "vector"));
        let costs = allowedVectors.map(vector => {
            let cost = this.additionalCostOfEffectAndVector(effectSlug, vector["slug"]);
            return cost - vector["giftCredit"] - effectGiftCredit;
        });
        if (costs.length > 1 ) {
            // will display cost on style selection.
            return null;
        }
        costs = costs.filter(cost => cost != 0);
        if (costs.length == 1) {
            return "(Gift Cost: " + displayCost(costs[0]) + ")";
        }
        return null;
      },
      getCostForVector(vectorSlug) {
        // the displayed cost for a vector is the combined cost of the effect and vector together.
        let credit = powerBlob.vectors[vectorSlug]["gift_credit"] + this.selectedEffect.giftCredit;
        let cost = this.additionalCostOfEffectAndVector(this.selectedEffect["slug"], vectorSlug) - credit;
        if (cost != 0) {
            return "(Gift Cost: " + displayCost(cost) + ")";
        }
        return null;
      },
      updateEffectFilters() {
          let allAvailableVectors = Array.from(new Set(this.effects
              .flatMap(effect => this.getAvailableVectorsForEffectAndModality(effect.slug, this.selectedModality.slug))));
          let newEffectFilters = [];
          newEffectFilters.push({
              id: "effect-filter-ALL",
              value: "ALL",
              display: "All",
          });
          this.effectFilters = newEffectFilters.concat(allAvailableVectors.map(vecSlug => vectorSlugToEffectFilter(vecSlug)));
          this.selectedEffectFilter = "ALL";
      },
      satisfiesEffectFilter(effectSlug) {
          if (this.selectedEffectFilter === "ALL") {
              return true;
          }
          let allAvailableVectors = this.getAvailableVectorsForEffectAndModality(effectSlug, this.selectedModality.slug);
          return allAvailableVectors.includes(this.selectedEffectFilter);
      },
      changeEffect(effect) {
          this.updateAvailableVectors();
          if (this.selectedEffectFilter != "ALL") {
              this.selectedVector = this.selectedEffectFilter;
          }
          this.componentClick();
          this.openCustomizationTab();
          this.scrollToTop();
      },
      updateAvailableVectors() {
          if (this.selectedEffect === null) {
              this.vectors = [];
              this.selectedVector = '';
              return;
          }
          const allowedVectors = this.getAvailableVectorsForEffectAndModality(this.selectedEffect.slug, this.selectedModality.slug);
          let unsortedVectors = Object.values(powerBlob.vectors)
              .filter(comp => allowedVectors.includes(comp.slug))
              .map(comp => componentToVue(comp, "vector"));
          this.vectors = sortVueModifiers(unsortedVectors);
          if (!allowedVectors.includes(this.selectedVector)) {
              this.selectedVector = this.vectors[0].slug;
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
      changeParam(param) {
          this.calculateRestrictedElements();
          this.reRenderSystemText();
          this.updateGiftCost();
      },
      componentClick() {
		if (this.selectedVector.length && this.selectedModality && this.selectedEffect) {
			this.populatePowerForm();
        }
      },
      getSelectedComponents() {
           return [
               powerBlob.modalities[this.selectedModality.slug],
               powerBlob.effects[this.selectedEffect.slug],
               powerBlob.vectors[this.selectedVector]
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
        this.systemFields = fieldsFromComponents(components, this.unrenderedSystem);
        this.systemFields.forEach(field => {
            if (field.isWeapon) {
                this.fieldWeaponInput[field.id] = field.weaponChoices[0][0];
            } else if (field.isRoll) {
                var defaultChoices = [field.attributeChoices[0][1]];
                if (field.abilityChoices.length > 0) {
                    defaultChoices.push(field.abilityChoices[0][1]);
                }
                this.fieldRollInput[field.id] = defaultChoices;
            } else {
                this.fieldTextInput[field.id] = "________";
            }
        });

        this.calculateRestrictedElements();
        this.reRenderSystemText();
        this.updateGiftCost();
        this.$nextTick(function () {
            activateTooltips();
        });
      },
      updateGiftCost() {
          let componentsCost = 1;
          this.getSelectedComponents().forEach(comp => {
              componentsCost = componentsCost - comp["gift_credit"];
          });
          componentsCost = componentsCost + this.additionalCostOfEffectAndVector(this.selectedEffect["slug"], this.selectedVector)

          let enhancementsCost = this.getSelectedAndActiveEnhancements().length
          let drawbacksCost = - this.getSelectedAndActiveDrawbacks().length;

          let parametersCost = 0;
          this.parameters.forEach(param => {
              parametersCost = parametersCost + giftCostOfVueParam(param, this.parameterSelections[param.id]);
          });
            // displayCost
          let toolTip = "Type, Effect, and Style: " + displayCost(componentsCost);
          toolTip = toolTip + (enhancementsCost != 0 ? "<br>Enhancements: " + displayCost(enhancementsCost) : "");
          toolTip = toolTip + (drawbacksCost != 0 ? "<br>Drawbacks: " + displayCost(drawbacksCost) : "");
          toolTip = toolTip + (parametersCost != 0 ? "<br>Parameters: " + displayCost(parametersCost) : "");
          this.giftCostTooltip = toolTip;
          this.giftCost = componentsCost + enhancementsCost + drawbacksCost + parametersCost;
          this.$nextTick(function () {
              activateTooltips();
          });
      },
      additionalCostOfEffectAndVector(effectSlug, vectorSlug) {
          let cost =0;
          powerBlob["effect_vector_gift_credit"].filter(cred => cred["vector"] === vectorSlug
                && cred["effect"] === effectSlug)
                .forEach(comp => {
                    cost= cost - comp["credit"];
                });
          return cost;
      },
      calculateRestrictedElements() {
          this.populateUniqueReplacementsMap();
          this.disabledEnhancements = {};
          this.disabledDrawbacks = {};
          this.disabledEnhancements = getDisabledModifiers("enhancement", this.enhancements, this.selectedEnhancements.map(slugFromVueModifierId), this.activeUniqueReplacementsByMarker);
          this.selectedEnhancements = this.selectedEnhancements.filter(mod => !(slugFromVueModifierId(mod) in this.disabledEnhancements));
          this.disabledDrawbacks = getDisabledModifiers("drawback", this.drawbacks, this.selectedDrawbacks.map(slugFromVueModifierId), this.activeUniqueReplacementsByMarker);
          this.selectedDrawbacks = this.selectedDrawbacks.filter(mod => !(slugFromVueModifierId(mod) in this.disabledDrawbacks));
          this.disabledParameters = {};
          this.disabledParameters = getDisabledParameters(this.parameters, this.activeUniqueReplacementsByMarker);

      },
      populateUniqueReplacementsMap() {
          // modifiers that have "unique" field replacements "block" modifiers that uniquely replace the same thing.
          this.activeUniqueReplacementsByMarker = {};
          this.getSelectedAndActiveEnhancements().concat(this.getSelectedAndActiveDrawbacks()).map(mod => slugFromVueModifierId(mod["id"])).forEach(mod => {
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
          let modSlug = slugFromVueModifierId(modifier.target.value);
          this.enhancements = handleModifierMultiplicity(modSlug, modifier.target.id, "enhancements", this.enhancements, this.getSelectedAndActiveEnhancements());
          this.calculateRestrictedElements();
          this.reRenderSystemText();
          this.updateGiftCost();
      },
      clickDrawback(modifier) {
          console.log("clicked Drawback");
          let modSlug = slugFromVueModifierId(modifier.target.value);
          this.drawbacks = handleModifierMultiplicity(modSlug, modifier.target.id, "drawbacks", this.drawbacks, this.getSelectedAndActiveDrawbacks());
          this.calculateRestrictedElements();
          this.reRenderSystemText();
          this.updateGiftCost();
      },
      reRenderSystemText() {
          const replacementMap = this.buildReplacementMap();
          this.renderedDescription = performSystemTextReplacements(this.unrenderedDescription, replacementMap);
          let partiallyRenderedSystem = performSystemTextReplacements(this.unrenderedSystem, replacementMap);
          this.renderedSystem = replaceHoverText(partiallyRenderedSystem);
          this.$nextTick(function () {
              activateTooltips();
          });
      },
      getSelectedAndActiveEnhancements() {
          return this.enhancements.filter(enh => this.selectedEnhancements.includes(enh["id"]));
      },
      getSelectedAndActiveDrawbacks() {
          return this.drawbacks.filter(drawb => this.selectedDrawbacks.includes(drawb["id"]));
      },
      buildReplacementMap() {
          // replacement marker to list of substitution objects
          replacements = {}
          addReplacementsForModifiers(replacements,
                                      this.getSelectedAndActiveEnhancements().map(mod => slugFromVueModifierId(mod["id"])).map(mod => powerBlob["enhancements"][mod]),
                                      buildModifierDetailsMap(this.getSelectedAndActiveEnhancements()));
          addReplacementsForModifiers(replacements,
                                      this.getSelectedAndActiveDrawbacks().map(mod => slugFromVueModifierId(mod["id"])).map(mod => powerBlob["drawbacks"][mod]),
                                      buildModifierDetailsMap(this.getSelectedAndActiveDrawbacks()));
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
              powerBlob["parameters"][parameter.id]["substitutions"].forEach(sub => {
                  const marker = sub["marker"];
                  var replacement = sub["replacement"];
                  if (replacement.includes("$")) {
                      replacement = replacement.replace("$", selection);
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
          });
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
                    sub = this.fieldTextInput[field.id];
                }
                if (field.isRoll) {
                    const choices = this.fieldRollInput[field.id];
                    sub = choices[0];
                    if (choices.length > 1) {
                        sub = sub + " + " + choices[1];
                    }
                }
                let replacement = field.replacement;
                if (replacement.includes("$")) {
                    replacement = field.isRoll ? replacement.replace("$", sub) : subUserInputForDollarSign(replacement, sub);
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
    mountedApp.modalities = Object.values(powerBlob.modalities).map(comp => componentToVue(comp, "mod"));
    mountedApp.$nextTick(function () {
      activateTooltips();
    });
    $('#giftPreviewModal').on('hidden.bs.modal', function (e) {
      mountedApp.giftPreviewModalFirstShow = false;
    })
});
