let characterData = null;
if (document.getElementById('characterBlob')) {
    characterData = JSON.parse(document.getElementById('characterBlob').textContent);
}
d10OutlineUrl = JSON.parse(document.getElementById('d10Outline').textContent);
d10FilledUrl = JSON.parse(document.getElementById('d10Filled').textContent);
timeline = null;
if (document.getElementById('timeline')) {
    timeline = JSON.parse(document.getElementById('timeline').textContent);
}

const charSheetRendering = {
  delimiters: ['{', '}'],
  data() {
    return {
      ready: false,
      character: null,
      showExtraStats: false,
      showTutorialText: true,
      showFieldValues: false,
      includePortrait: false,
      includeExpandedPowers: true,
      includeCraftedItems: true,
      includeCraftables: true,
      includeStory: true,
      includeTimeline: false,
      timeline: timeline,
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
    getNumInjuryPadding() {
        return Math.max(Math.max(this.character.mind - (this.character.body + 1), 0), 0);
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

const app = Vue.createApp(charSheetRendering);
const mountedApp = app.mount('#js-sheet-component');
mountedApp.character = characterData;
mountedApp.ready = true;