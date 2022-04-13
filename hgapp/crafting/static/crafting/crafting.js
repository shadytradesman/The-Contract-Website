let pageData = JSON.parse(JSON.parse(document.getElementById('pageData').textContent));
console.log(pageData);

function displayCost(cost) {
    let prefix =  cost >= 0 ? "-" : "+";
    let content = prefix + cost;
    let cssClass = cost < 0 ? "css-exp-credit" : cost == 0 ? "text-muted" : "css-exp-cost";
    return "<span class=\"" + cssClass +"\">" + content + " Exp</span>";
};

const CraftingRendering = {
  delimiters: ['{', '}'],
  data() {
    return {
      powers: [],
      consumableQuantities: {},
      consumableInitialQuantities: {},
      consumableExpCost: {},
      consumableNumFree: {},
      consumableNumWouldBeCrafted: {},
      consumableNumWouldBeRefunded: {},
      totalExpCost: "",
    }
  },
  methods: {
      setInitial() {
        console.log();
        for (const [powerId, value] of Object.entries(pageData["initial_consumable_counts"])) {
            this.consumableQuantities[powerId] = value;
            this.consumableExpCost[powerId] = 0;
        }
        for (const [powerId, numFree] of Object.entries(pageData["free_crafts_by_power_full"])) {
            this.consumableNumFree[powerId] = numFree;
        }
        for (const [powerId, initial] of Object.entries(pageData["initial_consumable_counts"])) {
            this.consumableInitialQuantities[powerId] = initial;
        }
        this.recalculateExpCosts();
      },
      incConsumable(powerId) {
        if ( this.consumableQuantities[powerId] < 20) {
            this.consumableQuantities[powerId] += 1;
        }
        this.recalculateExpCosts();
      },
      decConsumable(powerId) {
        if ( this.consumableQuantities[powerId] > 0) {
            this.consumableQuantities[powerId] -= 1;
        }
        this.recalculateExpCosts();
      },
      recalculateExpCosts() {
        let totalCost = 0;
        for (const [powerId, numCrafted] of Object.entries(this.consumableQuantities)) {
            this.consumableExpCost[powerId] = 0;
            this.consumableNumWouldBeCrafted = {};
            this.consumableNumWouldBeRefunded = {};
            let numPaidConsumables = Math.max(numCrafted - this.consumableNumFree[powerId], 0);
            let numInitialPaidConsumables = Math.max(this.consumableInitialQuantities[powerId] - this.consumableNumFree[powerId], 0);
            let expMultiple = Math.max(0, pageData["power_by_pk"][powerId]["gift_cost"]);
            let expDiff = (numPaidConsumables - numInitialPaidConsumables) * expMultiple
            totalCost += expDiff;
            this.consumableExpCost[powerId] = displayCost(expDiff);

            let prevCrafted = pageData["prev_crafted_consumables"][powerId];
            if (prevCrafted === undefined) {
                prevCrafted = 0;
            }
            let toCraftQuantity = numCrafted - prevCrafted;
            if (toCraftQuantity > 0) {
                this.consumableNumWouldBeCrafted[pageData["power_by_pk"][powerId]["name"]] = toCraftQuantity;
            }
            if (toCraftQuantity < 0) {
                this.consumableNumWouldBeRefunded[pageData["power_by_pk"][powerId]["name"]] = toCraftQuantity;
            }
        }
        this.totalExpCost = displayCost(totalCost);

      },
  }
}

function makeIncDecButtons(element, type) {
    let powerId = element.attr("data-power-id");
    element.append('<span @click="incConsumable('+powerId+')" class="inc val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-plus"></i></span>');
    element.prepend('<span @click="decConsumable('+powerId+')" class="dec val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-minus"></i></span>');
}

$(makeIncDecButtons($("span[class~='consumable-form']"), "consumable"));

const app = Vue.createApp(CraftingRendering);
const mountedApp = app.mount('#vue-app');
mountedApp.setInitial();
