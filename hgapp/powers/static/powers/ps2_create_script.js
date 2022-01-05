$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});


const powerBlob = JSON.parse(JSON.parse(document.getElementById('powerBlob').textContent));
console.log(powerBlob);
var unrenderedSystemText = "";

function componentToVue(component, type) {
    return {
        id: type + "-" + component.slug,
        slug: component.slug,
        displayName: component.name,
        summary: component.summary,
        type: component.type,
        giftCredit: component["gift_credit"],
    }
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
        description: modifier.description,
        detailLabel: modifier.detail_field_label === null ? false : modifier.detail_field_label,
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

function systemFieldToVue(systemField, isRoll) {
    const type = isRoll ? "roll" : "text";
    const attributeChoices = isRoll ? systemField["attribute_choices"] : [];
    const abilityChoices = isRoll ? systemField["ability_choices"] : [];
    return {
        id: type + systemField.id,
        marker: systemField.marker,
        replacement: systemField.replacement,
        name: systemField.name,
        eratta: systemField.eratta,
        isRoll: isRoll,
        isText: !isRoll,
        attributeChoices: attributeChoices,
        abilityChoices: abilityChoices,
    }
}

function modifiersFromComponents(components, modifier) {
    selectedModifierIds = components.flatMap(component => component[modifier]);
    blacklistModifierIds = components.flatMap(component => component["blacklist_" + modifier]);
    return selectedModifierIds.filter(x => !blacklistModifierIds.includes(x)).map(id => modifierToVue(powerBlob[modifier][id], modifier));
}

function paramsFromComponents(components, modifier) {
    powerParams = components.flatMap(component => component["parameters"]);
    return powerParams.map(param => powerParamToVue(param));
}

function fieldsFromComponents(components, unrenderedSystemText) {
    textFields = components.flatMap(component => component["text_fields"])
        .filter(field => unrenderedSystemText.includes(field["marker"]))
        .map(field => systemFieldToVue(field, false));
    rollFields = components.flatMap(component => component["roll_fields"])
        .filter(field => unrenderedSystemText.includes(field["marker"]))
        .map(field => systemFieldToVue(field, true));
    return textFields.concat(rollFields);
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
            let warningString = "Exclusive with " + activeUniqueReplacementsByMarker[sub["marker"]]["name"];
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
            .push("Exclusive with " + activeUniqueReplacementsByMarker[sub["marker"]]["name"]));
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

function addReplacementsForModifiers(replacements, selectedModifiers, detailsByModifiers) {
  let includedModSlugs = [];
  selectedModifiers
      .forEach(mod => {
          mod["substitutions"].forEach(sub => {
              const marker = sub["marker"];
              var replacement = sub["replacement"];
              let numIncludedForSlug = includedModSlugs.filter(includedSlug => includedSlug === mod["slug"]).length;
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
                      substitution = subStrings.join(", ");
                  } else {
                      substitution = detailsByModifiers[mod["slug"]][numIncludedForSlug];
                  }
                  replacement = replacement.replace("$", substitution);
                  includedModSlugs.push(mod["slug"]);
              }
              const newSub = {
                  mode: sub["mode"],
                  replacement: replacement,
              }
              if (mod["joining_strategy"] == "ALL" || numIncludedForSlug == 0) {
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
    '[': ' ',
    '{': '<br><br>',
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
//        console.log("replacing: ");
//        console.log(toReplace);
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
    var replacements = [];
    for (var i = 0; i < markers.length; i++) {
        if (markers[i] in replacementMap) {
            replacements = replacements.concat(replacementMap[markers[i]])
        }
    }

    var replacementText = "";
    if (replacements.length === 0 && toReplace.defaultValue) {
        replacementText = toReplace.defaultValue;
    }
    if (toReplace.type === '(') {
        replacements[0] = replacements[0][0].toUpperCase() + replacements[0].slice(1);
    }
    if (replacements.length === 1 ) {
        replacementText = replacements[0];
    }
    if (toReplace.type === '{') {
        replacements[0] = "<br><br>" + replacements[0];
    }
    if (replacements.length > 1) {
        if (toReplace.type === '(') {
            replacements[replacements.length - 1] = "and " + replacements[replacements.length - 1];
        }
        let joinString = parenJoinString[toReplace.type];
        if (toReplace.type == '(' && replacements.length == 2) {
            joinString = " ";
        }
        replacementText = replacements.join(joinString);
    }
    return systemText.slice(0, toReplace.start) + replacementText + systemText.slice(toReplace.end + 1);
}

const parenEndByStart = {
    '(': ')',
    '[': ']',
    '{': '}',
}
function findReplacementCandidate(systemText) {
    // Finds the first pair of opening parenthesis, indicating a replacement substring.
    // Proceeds to the matching closure of the parens, skipping any nested replacements
    // returns a little replacement candidate object.
    var markerStarts = ['(', '[', '{'];
    var endMarker = null;
    var parenDepth = 0;
    var parenType = null;
    var start = null;
    var end = null;
    var defaultContentStartIndex = null;
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
    const markerEnd = defaultContentStartIndex === null ? end - 1 : defaultContentStartIndex;
    var markerSection = systemText.slice(start + 2, markerEnd);
    markerSection = markerSection.trim();
    const markers = markerSection.split(',');
    if (markerStarts[0] != '(' && markers.length > 1) {
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
      modalities: [],
      selectedModality: "",
      effects: [],
      selectedEffect: "",
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
      unrenderedSystem: '',
      renderedSystem: '',
      activeUniqueReplacementsByMarker: {},
      giftCost: 0,
    }
  },
  methods: {
      clickModality(modality) {
          const allowed_effects = powerBlob["effects_by_modality"][this.selectedModality];
          this.effects = Object.values(powerBlob.effects)
              .filter(comp => allowed_effects.includes(comp.slug))
              .map(comp => componentToVue(comp, "effect"));
          if (!allowed_effects.includes(this.selectedEffect)) {
              this.selectedEffect = allowed_effects[0];
          }
          this.updateAvailableVectors();
          this.componentClick();
      },
      clickEffect(effect) {
          this.updateAvailableVectors();
          this.componentClick();
      },
      updateAvailableVectors() {
          if (this.selectedEffect.length == 0) {
              this.vectors = [];
              this.selectedVector = '';
              return;
          }
          const effect_vectors = powerBlob["vectors_by_effect"][this.selectedEffect];
          const modality_vectors = powerBlob["vectors_by_modality"][this.selectedModality];
          const allowed_vectors = effect_vectors.filter(x => modality_vectors.includes(x));
          this.vectors = Object.values(powerBlob.vectors)
              .filter(comp => allowed_vectors.includes(comp.slug))
              .map(comp => componentToVue(comp, "vector"));
          if (!allowed_vectors.includes(this.selectedVector)) {
              this.selectedVector = allowed_vectors[0];
          }
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
		if (this.selectedVector.length && this.selectedModality.length && this.selectedEffect.length) {
			this.populatePowerForm();
        }
      },
      getSelectedComponents() {
           return [
               powerBlob.modalities[this.selectedModality],
               powerBlob.effects[this.selectedEffect],
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
        this.unrenderedSystem = "<p>" + modality["system_text"] + "</p><p>" + vector["system_text"] + "</p><p>" + effect["system_text"] + "</p>";
        this.enhancements = modifiersFromComponents(components, "enhancements");
        this.drawbacks = modifiersFromComponents(components, "drawbacks");
        this.parameters = paramsFromComponents(components);
        this.parameters.forEach(param => {
            this.parameterSelections[param.id] = param.levels[param["defaultLevel"]];
        });
        this.systemFields = fieldsFromComponents(components, this.unrenderedSystem);
        this.systemFields.forEach(field => {
            if (field.isRoll) {
                var defaultChoices = [field.attributeChoices[0][1]];
                if (field.abilityChoices.length > 0) {
                    defaultChoices.push(field.abilityChoices[0][1]);
                }
                this.fieldRollInput[field.id] = defaultChoices;
            } else {
                this.fieldTextInput[field.id] = " ";
            }
        });

        this.calculateRestrictedElements();
        this.reRenderSystemText();
        this.updateGiftCost();
      },
      updateGiftCost() {
          let cost = 1 + this.selectedEnhancements.length - this.selectedDrawbacks.length;
          this.getSelectedComponents().forEach(comp => {
              cost = cost - comp["gift_credit"];
          });
          this.parameters.forEach(param => {
              cost = cost + giftCostOfVueParam(param, this.parameterSelections[param.id]);
          });
          this.giftCost = cost;
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
          this.selectedEnhancements.concat(this.selectedDrawbacks).map(slugFromVueModifierId).forEach(mod => {
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
          let mod = powerBlob["enhancements"][modSlug];
          // TODO: deduplicate with clickDrawback logic
          if (mod.multiplicity_allowed) {
              let numSelected = this.selectedEnhancements.map(slugFromVueModifierId).filter(enh => enh === modSlug).length;
              let numAvail = this.enhancements.filter(enh => enh["slug"] === modSlug).length;
              if (numSelected == numAvail && numAvail < 4) {
                  modCounter++;
                  this.enhancements.push(modifierToVue(mod, "enhancements", modCounter));
              } else if (numAvail - numSelected > 1){
                  this.enhancements = this.enhancements.filter(mod => mod["id"] != modifier.target.id);
              }
          }
          this.calculateRestrictedElements();
          this.reRenderSystemText();
          this.updateGiftCost();
      },
      clickDrawback(modifier) {
          console.log("clicked Drawback");
          let modSlug = slugFromVueModifierId(modifier.target.value);
          let mod = powerBlob["drawbacks"][modSlug];
          if (mod.multiplicity_allowed) {
              let numSelected = this.selectedDrawbacks.map(slugFromVueModifierId).filter(draw => draw === modSlug).length;
              let numAvail = this.drawbacks.filter(enh => enh["slug"] === modSlug).length;
              if (numSelected == numAvail && numAvail < 4) {
                  modCounter++;
                  this.drawbacks.push(modifierToVue(mod, "drawbacks", modCounter));
              } else if (numAvail - numSelected > 1){
                  this.drawbacks = this.drawbacks.filter(mod => mod["id"] != modifier.target.id);
              }
          }
          this.calculateRestrictedElements();
          this.reRenderSystemText();
          this.updateGiftCost();
      },
      reRenderSystemText() {
          const replacementMap = this.buildReplacementMap();
          this.renderedSystem = performSystemTextReplacements(this.unrenderedSystem, replacementMap);
      },
      buildReplacementMap() {
          // replacement marker to list of substitution objects
          replacements = {}
          addReplacementsForModifiers(replacements,
                                      this.selectedEnhancements.map(slugFromVueModifierId).map(mod => powerBlob["enhancements"][mod]),
                                      buildModifierDetailsMap(this.enhancements.filter(enh => this.selectedEnhancements.includes(enh["id"]))));
          addReplacementsForModifiers(replacements,
                                      this.selectedDrawbacks.map(slugFromVueModifierId).map(mod => powerBlob["drawbacks"][mod]),
                                      buildModifierDetailsMap(this.drawbacks.filter(enh => this.selectedDrawbacks.includes(enh["id"]))));
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
                  replacement = replacement.replace("$", sub);
              }
              replacements[field.marker].push({
                  replacement: replacement,
                  mode: "ADDITIVE",
              });
          })
      }
  }
}
const app = Vue.createApp(ComponentRendering);

const mountedApp = app.mount('#vue-app');

$(function() {
    mountedApp.modalities = Object.values(powerBlob.modalities).map(comp => componentToVue(comp, "mod"));
});
