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
      effects: [],
      vectors: [],
      enhancements: [],
      drawbacks: [],
      parameters: [],
      unrenderedSystem: '',
      renderedSystem: '',
    }
  },
  methods: {
      clickModality(modality) {
          const allowed_effects = powerBlob["effects_by_modality"][modality.slug];
          this.effects = Object.values(powerBlob.effects)
              .filter(comp => allowed_effects.includes(comp.slug))
              .map(comp => componentToVue(comp, "effect"));

          // Auto-check vectors if effects available.
          checkedEffects = $('input[name="EFFECT"]:checked');
          if (checkedEffects.length) {
              const slug = checkedEffects[0].value;
              checkedEffects = this.effects.filter(comp => comp.slug == slug);
              this.clickEffect(checkedEffects[0]);
          } else {
              this.vectors = [];
              this.selectedVector = '';
          }
          this.generalClick(modality);
      },
      clickEffect(effect) {
          const allowed_vectors = powerBlob["vectors_by_effect"][effect.slug];
          this.vectors = Object.values(powerBlob.vectors)
              .filter(comp => allowed_vectors.includes(comp.slug))
              .map(comp => componentToVue(comp, "vector"));
          this.generalClick(effect);
      },
      clickVector(component) {
          console.log("clicked vector");
          console.log(component.displayName);
          this.generalClick(component);
      },
      generalClick(component) {
        // TODO: figure out how to do this in a vue-y way.
		checkedModalities = $('input[name="MODALITY"]:checked');
		checkedEffects = $('input[name="EFFECT"]:checked');
		checkedVectors = $('input[name="VECTOR"]:checked');
		if (checkedEffects.length && checkedModalities.length && checkedVectors.length) {
			this.populatePowerForm(powerBlob.modalities[checkedModalities[0].value],
				powerBlob.effects[checkedEffects[0].value],
				powerBlob.vectors[checkedVectors[0].value]);
        }
      },
      populatePowerForm(modality, effect, vector) {
        this.unrenderedSystem = modality["system_text"] + "<br><br>" + vector["system_text"] + "<br><br>" + effect["system_text"] + "<br>";
        this.enhancements = modifiersFromComponents([modality, effect, vector], "enhancements");
        this.drawbacks = modifiersFromComponents([modality, effect, vector], "drawbacks");
//        this.parameters = modifiersFromComponents([modality, effect, vector], "parameters");
        this.reRenderSystemText();
      },
      clickEnhancement(component) {
          console.log("clicked Enhancement");
          this.reRenderSystemText();
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

const giftComponentTemplate = $('#js-gift-component-template').html();
const modifierTemplate= $('#js-modifier-template').html();

app.component('gift-component', {
  delimiters: ['{', '}'],
  props: ['component'],
  template: giftComponentTemplate
})

app.component('power-modifier', {
  delimiters: ['{', '}'],
  props: ['modifier'],
  template: modifierTemplate
})

const mountedApp = app.mount('#vue-app');

$(function() {
    mountedApp.modalities = Object.values(powerBlob.modalities).map(comp => componentToVue(comp, "mod"));
});
