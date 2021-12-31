const powerBlob = JSON.parse(JSON.parse(document.getElementById('powerBlob').textContent));
console.log(powerBlob);
var unrenderedSystemText = "";

function componentToVue(component, type) {
    return {
        id: type + "-" + component.slug,
        slug: component.slug,
        displayName: component.name,
        type: component.type
    }
}

function modifierToVue(modifier, type) {
    return {
        id: type + "-" + modifier.slug,
        slug: modifier.slug,
        displayName: modifier.name,
        description: modifier.description,
        detailLabel: modifier.detail_field_label === null ? false : modifier.detail_field_label,
    }
}

function powerParamToVue(powerParam) {
    return {
        id: powerParam.param_id,
        name: powerBlob["parameters"][powerParam.param_id]["name"],
        eratta: powerParam.eratta,
        defaultLevel: powerParam["default_level"],
        levels: powerParam.levels
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

function getDisabledModifiers(modType, availModifiers, selectedModifiers) {
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
       requiredSlugs = powerBlob[powerBlobFieldName][mod.slug][requiredFieldName];
       if (!(mod.slug in disabledModifiers)) {
           disabledModifiers[mod.slug] = [];
       }
       requiredSlugs.forEach(reqSlug => {
           disabledModifiers[mod.slug].push("Requires: " + powerBlob[powerBlobFieldName][reqSlug]["name"]);
       });
    });
    return disabledModifiers;
}

function addReplacementsForModifiers(replacements, selectedModifiers, detailsByModifiers) {
  selectedModifiers
      .forEach(mod => {
          mod["substitutions"].forEach(sub => {
              const marker = sub["marker"];
              var replacement = sub["replacement"];
              if (replacement.includes("$")) {
                  var subString = mod in detailsByModifiers ? detailsByModifiers[mod["slug"]] : "";
                  subString = subString.replace("((", "(");
                  subString = subString.replace("[[", "[");
                  subString = subString.replace("{{", "{");
                  subString = subString.replace("))", ")");
                  subString = subString.replace("]]", "]");
                  subString = subString.replace("}}", "}");
                  replacement = replacement.replace("$", subString);
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
          })
      });
}



const parenJoinString = {
    '(': ', ',
    '[': '. ',
    '{': '.<br>',
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
    if (replacements.length === 1 ) {
        replacementText = replacements[0];
    }
    if (replacements.length > 1) {
        if (toReplace.type === '(') {
            replacements[replacements.length - 1] = "and " + replacements[replacements.length - 1];
        }
        if (toReplace.type === '[' || toReplace.type === '{') {
            replacements = replacements.map(rep => rep[0].toUpperCase() + rep.slice(1));
        }
        replacementText = replacements.join(parenJoinString[toReplace.type]);
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
      detailsByEnhancements: {},
      disabledEnhancements: {}, // map of disabled enhancements slug to reason.
      drawbacks: [],
      selectedDrawbacks: [],
      detailsByDrawbacks: {},
      disabledDrawbacks: {}, // map of disabled drawback slug to reason.
      parameters: [],
      parameterSelections: {},
      unrenderedSystem: '',
      renderedSystem: '',
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
          this.reRenderSystemText();
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
        this.unrenderedSystem = modality["system_text"] + "<br><br>" + vector["system_text"] + "<br><br>" + effect["system_text"] + "<br>";
        this.enhancements = modifiersFromComponents(components, "enhancements");
        this.drawbacks = modifiersFromComponents(components, "drawbacks");
        this.parameters = paramsFromComponents(components);
        this.parameters.forEach(param => {
            this.parameterSelections[param.id] = param.levels[param["defaultLevel"]];
        });
        console.log(this.parameters);

//        this.parameters = modifiersFromComponents([modality, effect, vector], "parameters");

        this.calculateRestrictedModifiers();
        this.reRenderSystemText();
      },
      calculateRestrictedModifiers() {
          this.disabledEnhancements = {};
          this.disabledDrawbacks = {};
          this.disabledEnhancements = getDisabledModifiers("enhancement", this.enhancements, this.selectedEnhancements);
          this.selectedEnhancements = this.selectedEnhancements.filter(mod => !(mod in this.disabledEnhancements));
          this.disabledDrawbacks = getDisabledModifiers("drawback", this.drawbacks, this.selectedDrawbacks);
          this.selectedDrawbacks = this.selectedDrawbacks.filter(mod => !(mod in this.disabledDrawbacks));
      },
      clickEnhancement(component) {
          console.log("clicked Enhancement");
          this.calculateRestrictedModifiers();
          this.reRenderSystemText();
      },
      clickDrawback(component) {
          console.log("clicked Drawback");
          this.calculateRestrictedModifiers();
          this.reRenderSystemText();
      },
      reRenderSystemText() {
          const replacementMap = this.buildReplacementMap();
          this.renderedSystem = performSystemTextReplacements(this.unrenderedSystem, replacementMap);
      },
      buildReplacementMap() {
          // replacement marker to list of substitution objects
          replacements = {}
          addReplacementsForModifiers(replacements,
                                      this.selectedEnhancements.map(mod => powerBlob["enhancements"][mod]),
                                      this.detailsByEnhancements);
          addReplacementsForModifiers(replacements,
                                      this.selectedDrawbacks.map(mod => powerBlob["drawbacks"][mod]),
                                      this.detailsByDrawbacks);
          this.addReplacementsForComponents(replacements);
          this.addReplacementsForParameters(replacements);

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
          for (parameter in this.parameterSelections){
              const selection = this.parameterSelections[parameter];
              powerBlob["parameters"][parameter]["substitutions"].forEach(sub => {
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
          }
      }
  }
}
const app = Vue.createApp(ComponentRendering);

const mountedApp = app.mount('#vue-app');

$(function() {
    mountedApp.modalities = Object.values(powerBlob.modalities).map(comp => componentToVue(comp, "mod"));
});
