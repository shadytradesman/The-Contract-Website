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

function modifiersFromComponents(components, modifier) {
    selectedModifierIds = components.flatMap(component => component[modifier]);
    blacklistModifierIds = components.flatMap(component => component["blacklist_" + modifier]);
    return selectedModifierIds.filter(x => !blacklistModifierIds.includes(x)).map(id => modifierToVue(powerBlob[modifier][id], modifier));
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
      drawbacks: [],
      selectedDrawbacks: [],
      parameters: [],
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
      componentClick() {
		if (this.selectedVector.length && this.selectedModality.length && this.selectedEffect.length) {
			this.populatePowerForm(powerBlob.modalities[this.selectedModality],
				powerBlob.effects[this.selectedEffect],
				powerBlob.vectors[this.selectedVector]);
        }
      },
      populatePowerForm(modality, effect, vector) {
        console.log("updating power form with the following modality, effect and vector");
        console.log(modality);
        console.log(effect);
        console.log(vector);
        this.unrenderedSystem = modality["system_text"] + "<br><br>" + vector["system_text"] + "<br><br>" + effect["system_text"] + "<br>";
        this.enhancements = modifiersFromComponents([modality, effect, vector], "enhancements");
        this.drawbacks = modifiersFromComponents([modality, effect, vector], "drawbacks");
//        this.parameters = modifiersFromComponents([modality, effect, vector], "parameters");
        this.reRenderSystemText();
      },
      clickEnhancement(component) {
          console.log("clicked Enhancement");
          console.log(this.selectedEnhancements);
//          this.reRenderSystemText();
      },
      clickDrawback(component) {
          console.log("clicked Drawback");
          this.reRenderSystemText();
      },
      reRenderSystemText() {
          const replacementMap = this.buildReplacementMap();
          //TODO: implement
          unrenderedSystem = this.unrenderedSystem;
          this.renderedSystem = "";
      },
      buildReplacementMap() {
		checkedEnhancements = $('#js-enhancements-container').find('input:checked');
		console.log(checkedEnhancements);
		enhancementObjects = checkedEnhancements
            .map(function() {
                return powerBlob["enhancements"][this.getAttribute("slug")];
            });
        console.log(enhancementObjects);
		replacementByMarker = {};
		enhancementObjects.each(enhancement => {
            console.log(enhancement);
            enhancement["substitutions"].each(substitution => {
                if (null === substitution.replacement) {
                    substitution.replacement = enhancement.description;
                }
                replacementByMarker[substitution["marker"]] = substitution;
            })
		});
		console.log(replacementByMarker);
//		checkedEnhancements.each(enhancement => )

      }
  }
}
const app = Vue.createApp(ComponentRendering);

const mountedApp = app.mount('#vue-app');

$(function() {
    mountedApp.modalities = Object.values(powerBlob.modalities).map(comp => componentToVue(comp, "mod"));
});
