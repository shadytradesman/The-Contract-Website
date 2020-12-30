

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
        if (delta > {{character.unspent_rewards|length}}) {
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
</script>