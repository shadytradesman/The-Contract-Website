<script>

{% if requirements_json %}
    var modifier_requirements = {{ requirements_json | safe}};
{% else %}
    var modifier_requirements = "";
{% endif %}
{% if spent_rewards_json %}
    var spent_rewards = {{ spent_rewards_json | safe}};
{% endif %}
{% if unspent_rewards_json %}
    var unspent_rewards = {{ unspent_rewards_json | safe}};
{% endif %}

var systemDefaultText = JSON.parse(document.getElementById('defaultSystem').textContent);
$(document).on('click', "#reset-system-text-button", function(ev){
    console.log(systemDefaultText);
    $("#id_system").val(systemDefaultText);
})

// Enhancement checkbox creation / deletion for multiplicity
var checkbox_incrementer=0;
$(document).on('change','[id$=-is_selected]', function(ev){
        if (this.parentElement.parentElement.parentElement.className == "non-multiple") {
            return true;
        }
        ev.preventDefault();
        var parent = this.parentElement.parentElement.parentElement;
        var count = parent.parentElement.children.length;
        var modifierSlug = parent.parentElement.id;
        var tmplMarkup = $('#'+modifierSlug+"-template").html();
        var compiledTmpl = tmplMarkup.replace(/__prefix__/g, checkbox_incrementer++);
        var maxEnhancements = 4;
        getGiftCost()
        if (this.checked && count < maxEnhancements){
            console.log(parent.id);
            $("#" + modifierSlug).append(compiledTmpl);
            $('#id_item_items-TOTAL_FORMS').attr('value', count+1);
        } else if (!this.checked && (count > 1)) {
            $("#" + parent.id).remove();
            $('#id_item_items-TOTAL_FORMS').attr('value', count-1);
        }
});

$(document).on('change','[id$=-is_selected], [id$=-level_picker]', function(ev){
    updateGiftCost();
});

$(document).on('change','[id$=-is_selected]', function(ev) {
    checkModifierRequirements();
});

window.onload = updateGiftCost();
window.onload = checkModifierRequirements();

function updateGiftCost() {
    gift_cost = getGiftCost();
    $('#current_gift_cost_number').text(gift_cost);
    delta = gift_cost - {% if og_power %} {{og_power.get_point_value}} {% else %} 0 {% endif %};
    delta_text = delta.toString();
    if (delta >= 0) {
        delta_text = "+" + delta_text;
    }
    $('#gift_cost_delta').text(delta_text);
    {% if character %}
        if (delta > {{character.num_unspent_rewards}}) {
            $('#gift_cost_delta').css("color", "red");
        } else if (delta < 0) {
            $('#gift_cost_delta').css("color", "white");
        } else if (delta > 0) {
            $('#gift_cost_delta').css("color", "green");
        } else {
            $('#gift_cost_delta').css("color", "white");
        }
        $('#gifts_affected').text("");
        if (delta > 0 && delta > unspent_rewards.length) {
            $('.js-gift-warn').show();
            $('.js-gift-info').hide();
        } else if (delta > 0 ) {
            $('.js-gift-warn').hide();
            $('.js-gift-info').show();
            $('#gift_cost_summary').text("Finalizing will cost the following gifts:");
            for (index = 0; index < delta; index++) {
                if (index > unspent_rewards.length -1) {
                    break;
                } else {
                     $('#gifts_affected').append("<li>"  + unspent_rewards[index] + "</li>");
                }
            }
        } else if (delta < 0) {
            $('.js-gift-warn').hide();
            $('.js-gift-info').show();
            $('#gift_cost_summary').text("Finalizing will refund the following gifts:");
            for (index = 0; index < delta*-1; index++) {
                if (index > spent_rewards.length -1) {
                    break;
                } else {
                     $('#gifts_affected').append("<li>"  + spent_rewards[index] + "</li>");
                }
            }
        } else {
             $('.js-gift-warn').hide();
             $('.js-gift-info').show();
             $('#gift_cost_summary').text("Finalizing will not affect gifts");
             $('#gifts_affected').text("");
        }
    {% endif %}

}

function checkModifierRequirements() {
    $(".js_modifier_requirements").html("");
    $( "[id$=-is_selected]" ).each(function() {
        var modifier = $( this );
        for (index = 0; index < modifier_requirements[modifier.attr('name')].length; ++index) {
            var required_modifier_name = modifier_requirements[modifier.attr('name')][index];
            var required_modifier = $('[name=' + required_modifier_name +']').first();
            var required_modifier_readable = required_modifier.attr("data-name");
            if (!required_modifier[0].checked){
                modifier.prop("checked", false);
                modifier.parent().parent()
                    .addClass("text-muted");
                modifier.parent().parent()
                    .find('input')
                    .attr("disabled", true);
                modifier.attr("disabled", true);
                var current_requirements = modifier.parent().parent()
                    .find(".js_modifier_requirements")
                    .html();
                current_requirements = current_requirements.length > 0 ? current_requirements + ", " + required_modifier_readable : "Requires: " + required_modifier_readable;
                modifier.parent().parent()
                    .find(".js_modifier_requirements")
                    .html(current_requirements);
            } else {
                modifier.removeAttr("disabled");
                modifier.parent().parent()
                        .find('input')
                        .removeAttr("disabled");
                modifier.parent().parent()
                        .removeClass("text-muted");
                modifier.parent().parent()
                    .find(".js_modifier_requirements")
                    .html("");
            }
        }
    });
}

function getGiftCost() {
    var num_checked_enhancements = document.querySelectorAll('.enhancements input[type="checkbox"]:checked').length
    var num_checked_drawbacks = document.querySelectorAll('.drawbacks input[type="checkbox"]:checked').length
    var total_current_param_values = 0;
    $.each($("[id$=-level_picker]") ,function() {
        total_current_param_values += parseInt($(this).val());
    });
    var defaultText = "(Default)";
    $.each($('[id$=-level_picker]').find('option:contains('+defaultText+')'),function() {
        total_current_param_values -= this.value;
    });
    return num_checked_enhancements - {{ base_power.num_free_enhancements }} - num_checked_drawbacks + total_current_param_values + 1;
}

// example power toggle
var examplesShown = false;
$(document).on('click','#js-example-power-button', function() {
    examplesShown = !examplesShown;
    if (examplesShown) {
        $("#js-example-power-button").text("Hide Examples");
    } else {
        $("#js-example-power-button").text("Show Examples");
    }
});

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});

$(document).on('click','#js-system-edit-button', function() {
    $("#js-system-form").show();
    $("#js-system-edit-button").hide();
    $(".js-system-static").hide();
});

$(document).ready(function(){

    var wasMindBodyLast = [];

    function setMindBody(id, isMindBody) {
        var select = $("select[id$=" + id + "-ability_roll]");
        var options = select.children("option");
        if (options.length == 0) {
            console.log("No ability field");
            return;
        }
        var opt1 = select.children("option").get(1).value;
        if (wasMindBodyLast[id] != isMindBody) {
            console.log("Setting children of " + id + " to " + isMindBody);
            if (isMindBody) {
                select.val('');
            } else {
                select.val(opt1);
            }
        }
        if (select.val() == '' && !isMindBody) {
            select.val(opt1);
        }
        select.children("option").prop('disabled', isMindBody);
        select.children("option[value='']").prop('disabled', !isMindBody);
        wasMindBodyLast[id] = isMindBody;
    }

    function setParrySpeed(attr_field, isParry) {
        const defaultSpeed = $(attr_field).parent().parent().find(".js-roll-field-speed-val-default");
        const parrySpeed = $(attr_field).parent().parent().find(".js-roll-field-speed-val-parry");
        if (isParry) {
            defaultSpeed.hide();
            parrySpeed.show();
        } else {
            defaultSpeed.show();
            parrySpeed.hide();
        }
        console.log("Default speed: ");
        console.log(defaultSpeed);
    }

    function updateSelectableRoll(attr_roll) {
        var idNum = get_id(attr_roll);
        if (attr_roll.value == "BODY" || attr_roll.value == "MIND" || attr_roll.value == "PARRY") {
            setMindBody(idNum, true);
        } else {
            setMindBody(idNum, false);
        }
        if (attr_roll.value == "PARRY") {
            setParrySpeed(attr_roll, true);
        } else {
            setParrySpeed(attr_roll, false);
        }
    }

    function get_id(attr_roll) {
        var regex = ".*([\\d]).*";
        var idString = $(attr_roll).attr('id');
        return idString.toString().match(regex)[1];
    }

    $("select[id$=-attribute_roll]").change(function () {
        updateSelectableRoll(this);
    });

    $("select[id$=-attribute_roll]").each(function() {
        var id = get_id(this);
        if (this.value == "BODY" || this.value == "MIND") {
            wasMindBodyLast[id] = true;
        } else {
            wasMindBodyLast[id] = false;
        }
        updateSelectableRoll(this);

    });

  });

</script>