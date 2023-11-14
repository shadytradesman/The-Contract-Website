let data = null;
if (document.getElementById('rulesData')) {
    data = JSON.parse(document.getElementById('rulesData').textContent);
    d10OutlineUrl = data["d10_outline_url"];
    d10FilledUrl = data["d10_filled_url"];
}

const quickstartRendering = {
  delimiters: ['{', '}'],
  data() {
    return {
      ready: false,

      showExtraStats: false,
      showTutorialText: true,

      showExpLog: true,
      showExpLogDefault: true,

      showNewCharacterGuide: true,
      showLimitsAndStats: true,
      showAssetsAndLiabilities: true,

      tutorial: null,
      abilities: null,
      attributes: null,
      limits: null,
      assets: null,
      liabilities: null,
    }
  },
  methods: {
    displayValue(val, normalMax) {
        let filledD10 = '<img class="d10-filled" src="' + d10FilledUrl + '" width="40" height="40" >'
        let outlineD10 = '<img class="d10-outline" src="' + d10OutlineUrl + '" width="40" height="40" >'
        return filledD10.repeat(Math.max(0, val)) + outlineD10.repeat(Math.max(0, normalMax-val));
    },
    getPenalty(max, row) {
        const penalties = ['-1', '-1', '-2', '-3', '-4', 'X_X'];
        return max - row + 1 <= penalties.length ? penalties[penalties.length - (max - row + 1)] : "-0";
    },
    useTwoStatsPages() {
        let numCircumstances = this.character.circumstances.length
        let numConditions = this.character.conditions.length
        let hasLongWorldElements = (this.showTutorialText && (numConditions > 2 || numCircumstances > 2))
        let hasManyWorldElements = numConditions > 5 || numCircumstances > 5
        return this.includePortrait || hasLongWorldElements || hasManyWorldElements;
    },
  }
}

const app = Vue.createApp(quickstartRendering);
const mountedApp = app.mount('#js-sheet-component');
mountedApp.tutorial = data["tutorial"];
mountedApp.attributes = data["attributes"];
mountedApp.abilities = data["abilities"];
mountedApp.ready = true;
