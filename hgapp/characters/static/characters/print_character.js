let characterData = {};
if (document.getElementById('characterBlob')) {
    characterData = JSON.parse(document.getElementById('characterBlob').textContent);
}

const charSheetRendering = {
  delimiters: ['{', '}'],
  data() {
    return {
      ready: false,
      character: null,
      showExtraStats: true,
      showAdvancementCosts: true,
    }
  },
  methods: {
    displayValue(val, normalMax) {
        return '<span class="dot-filled"></span>'.repeat(Math.max(0, val)) + '<span class="dot"></span>'.repeat(Math.max(0, normalMax-val));
    }
  }
}

const app = Vue.createApp(charSheetRendering);
const mountedApp = app.mount('#js-sheet-component');
mountedApp.character = characterData;
mountedApp.ready = true;