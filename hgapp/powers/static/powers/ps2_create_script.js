const powerBlob = JSON.parse(JSON.parse(document.getElementById('powerBlob').textContent));
var unrenderedSystemText = "";

function componentToVue(component, type) {
    return {
        id: type + "-" + component.slug,
        slug: component.slug,
        displayName: component.name,
        type: component.type
    }
}

function modifiersFromComponents(components, modifier) {
    selectedModifierIds = components.flatMap(component => component[modifier]);
    blacklistModifierIds = components.flatMap(component => component["blacklist_" + modifier]);
    return selectedModifierIds.filter(x => !blacklistModifierIds.includes(x)).map(id => powerBlob[modifier][id]);
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
      renderedSystem: ''
    }
  },
  methods: {
      clickModality(component) {
          const allowed_effects = powerBlob["effects_by_modality"][component.slug];
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
          this.$nextTick(this.generalClick(component))
      },
      clickEffect(component) {
          const allowed_vectors = powerBlob["vectors_by_effect"][component.slug];
          this.vectors = Object.values(powerBlob.vectors)
              .filter(comp => allowed_vectors.includes(comp.slug))
              .map(comp => componentToVue(comp, "vector"));
          this.$nextTick(this.generalClick(component));
      },
      clickVector(component) {
          console.log("clicked vector");
          console.log(component.displayName);
          this.$nextTick(this.generalClick(component));
      },
      generalClick(component) {
        // TODO: figure out how to do this in a vue-y way.
		checkedModalities = $('input[name="MODALITY"]:checked');
		checkedEffects = $('input[name="EFFECT"]:checked');
		checkedVectors = $('input[name="VECTOR"]:checked');
		console.log(checkedVectors);
		if (checkedEffects.length && checkedModalities.length && checkedVectors.length) {
			console.log("all three!");
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
        console.log(this.enhancements);
        console.log(this.drawbacks);
//        console.log(this.parameters);

        this.reRenderSystemText();
      },
      reRenderSystemText() {
          //TODO: implement
          this.renderedSystem = "";
      }
  }
}
const app = Vue.createApp(ComponentRendering);

const giftComponentTemplate = $('#js-gift-component-template').html();
const modifierTemplate= $('#js-modifier-template').html();

app.component('gift-component', {
  delimiters: ['{', '}'],
  props: ['component'],
  data() {
    return {
        selected: ''
    }
  },
  template: giftComponentTemplate
})

const mountedApp = app.mount('#vue-app');

$(function() {
    mountedApp.modalities = Object.values(powerBlob.modalities).map(comp => componentToVue(comp, "mod"));
});
