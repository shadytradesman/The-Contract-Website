$(function() {
    $("span[class~='ability-form']").append('<span class="inc val-adjuster btn btn-default btn-xs"><i class="fa fa-plus"></i></span>');
    $("span[class~='ability-form']").prepend('<span class="dec val-adjuster btn btn-default btn-xs"><i class="fa fa-minus"></i></span>');
});

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

$(document).on('keypress','[class~=sec-ability-name]', function(ev){
    console.log("blah");
    var parent = this.parentElement.parentElement.parentElement;
    var count = parent.parentElement.children.length;
    var modifierSlug = parent.parentElement.id;
    var tmplMarkup = $('#'+modifierSlug+"-template").html();
    var compiledTmpl = tmplMarkup.replace(/__prefix__/g, checkbox_incrementer++);
    var maxEnhancements = 4;
    if (this.checked && count < maxEnhancements){
        console.log(parent.id);
        $("#" + modifierSlug).append(compiledTmpl);
        $('#id_item_items-TOTAL_FORMS').attr('value', count+1);
    } else if (!this.checked && (count > 1)) {
        $("#" + parent.id).remove();
        $('#id_item_items-TOTAL_FORMS').attr('value', count-1);
    }
});