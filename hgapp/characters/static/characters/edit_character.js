function makeIncDecButtons(element) {
    element.append('<span class="inc val-adjuster btn btn-default btn-xs"><i class="fa fa-plus"></i></span>');
    element.prepend('<span class="dec val-adjuster btn btn-default btn-xs"><i class="fa fa-minus"></i></span>');
}

$(makeIncDecButtons($("span[class~='ability-form']")));

$(document).on("click", ".val-adjuster", function() {
  var button = $(this);
  var oldValue = button.parent().find("input").val();
  var newValue = 0;

  if (button.hasClass("inc")) {
      if (oldValue < 5) {
        newValue = parseFloat(oldValue) + 1;
      }
      else {
	     newValue = 5;
	  }
	} else {
    if (oldValue > 0) {
      newValue = parseFloat(oldValue) - 1;
    } else {
      newValue = 0;
    }
  }
  button.parent().find("input").val(newValue);
});

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});

// Secondary ability creation / destruction
var secondary_inc = 0;
$(document).on('change','[class~=sec-ability-name]', function(ev){
    var numSecondaries = $('[class~=sec-ability-name]').length;
    var emptySecondaries = $('[class~=sec-ability-name]').filter(function() {return !this.value;});
    var numEmptySecondaries = emptySecondaries.length;

    if (numEmptySecondaries > 1) {
        emptySecondaries[0].parentElement.parentElement.remove();
        $('#id_item_items-TOTAL_FORMS').attr('value', numSecondaries-1);
    } else if (numEmptySecondaries == 0) {
        var tmplMarkup = $('#sec-ability-template').html();
        var compiledTmpl = tmplMarkup.replace(/__prefix__/g, ++secondary_inc);
        var elem = $("#extra-secondaries").append(compiledTmpl);
        makeIncDecButtons($("span[id=secondary-ability-form-" + secondary_inc + "]"));
        $('#id_item_items-TOTAL_FORMS').attr('value', numSecondaries + 1);
    }
});

// toggle-y buttons
$('.btn').button();
$(".btn").mouseup(function(){
    $(this).blur();
})

// Quirk creation / destruction
// Enhancement checkbox creation / deletion for multiplicity
var quirk_inc =0;
$(document).on('change','[id$=-is_selected]', function(ev){
        var checkbox = $(this);
        if (checkbox.hasClass("quirk-multiple-False")) {
            return true;
        }
        var checkboxGroup = checkbox.closest(".quirk-group-container");
        var isLiability = checkboxGroup.children("[id^=liability]").length > 0;

        var count = checkboxGroup.children().length; //subtract 1 for extra <br> element too
        var quirkId = checkboxGroup.attr('id').slice(6);
        var emptyCheckboxes = $('[class~=btn-'+ (isLiability ? "True" : "False") +'-'+ quirkId + ']:not([class~=active])')
//        console.log(count);
        console.log(quirkId);
        console.log(emptyCheckboxes);
        if (isLiability) {
            var tmplMarkup = $('#liability-'+quirkId+"-template").html();
        } else {
            var tmplMarkup = $('#asset-'+quirkId+"-template").html();
        }
        var compiledTmpl = tmplMarkup.replace(/__prefix__/g, ++count);
        var maxOfOneQuirk = 4;
        if (this.checked && count < maxOfOneQuirk){
            var newBox = checkboxGroup.append(compiledTmpl);
            if(compiledTmpl.includes("wiki-entry-collapsible")) {
                    var collapsibleContainer = newBox.find('[class~=wiki-entry-collapsible]').get(count-1);
                    setupCollapsibles(collapsibleContainer);
            }
            $('#id_item_items-TOTAL_FORMS').attr('value', count+1);
        } else if (!this.checked && (count > 1) && emptyCheckboxes.length>1) {
            checkbox.closest('[id^=' + (isLiability ? 'liability' : 'asset') + '-'+quirkId+']').remove();
            $('#id_item_items-TOTAL_FORMS').attr('value', count-1);
        }
});