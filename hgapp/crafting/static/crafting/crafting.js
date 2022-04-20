let pageData = JSON.parse(JSON.parse(document.getElementById('pageData').textContent));
console.log(pageData);

function displayCost(cost) {
    let prefix =  cost >= 0 ? "-" : "+";
    let content = prefix + Math.abs(cost).toString();
    let cssClass = cost < 0 ? "css-exp-credit" : cost == 0 ? "text-muted" : "css-exp-cost";
    return "<span class=\"" + cssClass +"\">" + content + " Exp</span>";
};

function createGiftOption(powerName, powerId, cost, giftOptionsName, number, checked) {
    return {
        "name": giftOptionsName + "_" + number,
        "value": powerId,
        "label": powerName,
        "cost": cost,
        "currentCost": "",
        "startChecked": checked,
    };
}

let newArtifactNumber = -1;
let artNum = 0;
let giftSelectorNumber = 0;

function createArtifactFromExisting(name, description, id, nonRefundablePowerIds, refundablePowerIds) {
    let number = artNum;
    artNum++;
    return createArtifact(true, name, description, number, id, nonRefundablePowerIds, refundablePowerIds);
}

function createNewArtifact() {
    let number = artNum;
    artNum++;
    newArtifactNumber++;
    let idVal = -(number+1);
    return createArtifact(false, "New Artifact", "", number, idVal, [], []);
}

function createArtifact(isPreExisting, name, description, number, id, nonRefundablePowerIds, refundablePowerIds) {
    let newArtForm = $("#empty_new_art_form").html();
    let giftSelectForm = $("#empty_gift_selector_id_form").html();
    let selectorNumber = giftSelectorNumber;
    let giftOptionsName = "gift_selector-" + selectorNumber + "-selected_gifts";
    giftSelectorNumber++;
    let optionNumber = 0;
    nonRefundablePowerFulls = nonRefundablePowerIds.map(id=>pageData["power_by_pk"][id])
    let giftOptions = pageData["artifact_power_choices"]
        .filter(choice => !nonRefundablePowerIds.includes(choice["pk"]))
        .map(choice => {
            let powerId = choice["pk"];
            let powerName = choice["name"];
            let cost = pageData["power_by_pk"][powerId]["gift_cost"] + 1;
            return createGiftOption(powerName, powerId, cost, giftOptionsName, optionNumber++, refundablePowerIds.includes(choice["pk"]));
        });
    return {
        "isPreExisting": isPreExisting,
        "number": number,
        "newArtNum": newArtifactNumber,
        "giftSelectForm": giftSelectForm,
        "newArtForm": newArtForm,
        "selectorNumber": selectorNumber,
        "name": name,
        "description": description,
        "giftOptions": giftOptions,
        "giftOptionsName": giftOptionsName,
        "id": id, // for linking artifacts with forms.
        "nonRefundablePowerFulls": nonRefundablePowerFulls,
    };
}

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
      artifacts: [],
      artifactPowerChoices: [],
      numNewArtifacts: 0,
      checkedGiftOptions: {},
      unavailArtifacts: [],
      freeArtCraftingGifts: []
    }
  },
  methods: {
      setInitial() {
        for (const [powerId, value] of Object.entries(pageData["initial_consumable_counts"])) {
            this.consumableQuantities[powerId] = value;
            this.consumableExpCost[powerId] = 0;
        }
        for (const [powerId, numFree] of Object.entries(pageData["free_crafts_by_power_full"])) {
            this.consumableNumFree[powerId] = numFree;
            let power = pageData["power_by_pk"][powerId];
            if (numFree > 0 && power["crafting_type"] == "ARTIFACT_CRAFTING") {
                this.freeArtCraftingGifts.push({
                    "power": power,
                    "numFree": numFree
                });
            }
        }
        for (const [powerId, initial] of Object.entries(pageData["initial_consumable_counts"])) {
            this.consumableInitialQuantities[powerId] = initial;
        }
        this.unavailArtifacts = pageData["artifacts_out_of_pos"];
        this.artifacts = pageData["existing_artifacts"]
                .map(art => createArtifactFromExisting(
                    art["name"],
                    art["description"],
                    art["id"],
                    art["nonrefundable_power_fulls"],
                    art["refundable_power_fulls"]));
        this.artifacts.forEach(art => art["giftOptions"].forEach(opt => {
            if (opt["startChecked"]) {
                this.checkedGiftOptions[opt["name"]] = true;
            }
        }))

        this.updateManagementForms();
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
        // Consumables
        this.consumableNumWouldBeCrafted = {};
        this.consumableNumWouldBeRefunded = {};
        for (const [powerId, numCrafted] of Object.entries(this.consumableQuantities)) {
            this.consumableExpCost[powerId] = 0;
            let numPaidConsumables = Math.max(numCrafted - this.consumableNumFree[powerId], 0);
            let numInitialPaidConsumables = Math.max(this.consumableInitialQuantities[powerId] - this.consumableNumFree[powerId], 0);
            let consumableExpMultiple = 2;
            let expDiff = (numPaidConsumables - numInitialPaidConsumables) * consumableExpMultiple;
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

        // Artifacts
        let num_crafted_by_power_id = {};
        this.artifacts.forEach(art => {
            art["giftOptions"].forEach(opt => {
                let currentlyChecked = this.checkedGiftOptions[opt["name"]];
                let cost = parseInt(opt["cost"]);
                if (currentlyChecked || opt["startChecked"]) {
                    if ( !(opt["value"] in num_crafted_by_power_id)) {
                        num_crafted_by_power_id[opt["value"]] = 0;
                    }
                    if (currentlyChecked) {
                        num_crafted_by_power_id[opt["value"]] = num_crafted_by_power_id[opt["value"]] + 1;
                    }
                    if (num_crafted_by_power_id[opt["value"]] < pageData["free_crafts_by_power_full"][opt["value"]]) {
                        cost = 0;
                    }
                }
                if (opt["startChecked"]) {
                    if (currentlyChecked) {
                        opt["currentCost"] = "";
                    } else {
                        totalCost -= cost;
                        opt["currentCost"] = displayCost(-cost);
                    }
                } else {
                    if (currentlyChecked) {
                        totalCost += cost;
                        opt["currentCost"] = displayCost(cost);
                    } else {
                        opt["currentCost"] = "";
                    }
                }
            })
        });
        this.totalExpCost = displayCost(totalCost);
      },
      newArtifact() {
        this.artifacts.unshift(createNewArtifact());
        this.numNewArtifacts ++;
        this.updateManagementForms();
      },
      updateManagementForms() {
          $('#id_new_artifact-TOTAL_FORMS').attr('value', this.numNewArtifacts);
          $('#id_gift_selector-TOTAL_FORMS').attr('value', this.artifacts.length);
      }
  }
}

function makeIncDecButtons(element, type) {
    let powerId = $(element).attr("data-power-id");
    $(element).append('<span @click="incConsumable('+powerId+')" class="inc val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-plus"></i></span>');
    $(element).prepend('<span @click="decConsumable('+powerId+')" class="dec val-adjuster-'+type+' btn btn-default btn-xs"><i class="fa fa-minus"></i></span>');
}

$($("span[class~='consumable-form']").each((i,e) => {makeIncDecButtons(e, "consumable")}));

const app = Vue.createApp(CraftingRendering);
const mountedApp = app.mount('#vue-app');
mountedApp.setInitial();
