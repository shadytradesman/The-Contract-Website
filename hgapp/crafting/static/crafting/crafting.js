let pageData = JSON.parse(JSON.parse(document.getElementById('pageData').textContent));
console.log(pageData);

function displayCost(cost) {
    let prefix =  cost >= 0 ? "-" : "+";
    let content = prefix + cost;
    let cssClass = cost < 0 ? "css-exp-credit" : cost == 0 ? "text-muted" : "css-exp-cost";
    return "<span class=\"" + cssClass +"\">" + content + " Exp</span>";
};

function createGiftOption(powerName, powerId, giftOptionsName, number) {
    return {
        "name": giftOptionsName + "_" + number,
        "value": powerId,
        "label": powerName
    };
}

let artifactNumber = 0;

function createArtifactFromExisting(name, description, id) {
    let number = artifactNumber;
    artifactNumber++;
    return createArtifact(true, name, description, number, id, []);
}

function createNewArtifact() {
    let number = artifactNumber;
    artifactNumber++;
    let idVal = -(number+1);
    return createArtifact(false, "New Artifact", "", number, idVal, []);
}

// This method sets the __prefix__ values that appear in django "empty" formset forms so formsets
// can have dynamically added and subtracted entries
function setFormInputPrefixValues() {
    $(".js-data-prefix-container").each(function(){
        let prefixNum = $(this).attr("data-prefix");
        $(this).find("input").each(function() {
            let currName = $(this).attr("name");
            let currId = $(this).attr("id");
            $(this).attr("name", currName.replace(/__prefix__/g, prefixNum));
            $(this).attr("id", currId.replace(/__prefix__/g, prefixNum));
        })
        $(this).find("label").each(function() {
            let currFor = $(this).attr("for");
            $(this).attr("for", currFor.replace(/__prefix__/g, prefixNum));
        })
    })
}

function createArtifact(isPreExisting, name, description, number, id, existingAttachedPowerFulls) {
    let giftOptionsName = "gift_selector-" + number + "-selected_gifts";
    let optionNumber = 0;
    let giftOptions = pageData["artifact_power_choices"]
        .filter(choice => !existingAttachedPowerFulls.includes(choice["pk"]))
        .map(choice => {
            let powerId = choice["pk"];
            let powerName = choice["name"];
            return createGiftOption(powerName, powerId, giftOptionsName, optionNumber++);
        });
    return {
        "isPreExisting": false,
        "number": number,
        "name": name,
        "description": description,
        "giftOptions": giftOptions,
        "giftOptionsName": giftOptionsName,
        "id": id, // for linking artifacts with forms.
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
        }
        for (const [powerId, initial] of Object.entries(pageData["initial_consumable_counts"])) {
            this.consumableInitialQuantities[powerId] = initial;
        }
        pageData["artifact_power_choices"].map(choice => { })
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
        this.totalExpCost = displayCost(totalCost);
      },
      newArtifact() {
        this.artifacts.push(createNewArtifact());
        this.numNewArtifacts ++;
        this.updateManagementForms();
        this.$nextTick(function () {
            setFormInputPrefixValues();
        });
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
