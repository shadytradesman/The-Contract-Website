var elemData = JSON.parse(document.getElementById('elementData').textContent);

$("#id_premade_element_field").change(function (e) {
    let selectedOption = e.target.options[e.target.selectedIndex];
    let nameField = $(e.target).closest(".js-world-element-form").find("#id_name");
    let detailsField = $(e.target).closest(".js-world-element-form").find("#id_details");
    let threatField = $(e.target).closest(".js-world-element-form").find("#id_threat");
    let threatLevelField = $(e.target).closest(".js-world-element-form").find("#id_threat_level");
    let howToTieUpField = $(e.target).closest(".js-world-element-form").find("#id_how_to_tie_up");
    let cutoffField = $(e.target).closest(".js-world-element-form").find("#id_cutoff");
    let selectedName = selectedOption.text;
    if (selectedOption.value.length > 0) {
        nameField.val(selectedName);
        detailsField.val(elemData[selectedName]["description"]);
        threatField.val(elemData[selectedName]["system"]);
        threatLevelField.val(elemData[selectedName]["threat_level"]);
        howToTieUpField.val(elemData[selectedName]["how_to_tie_up"]);
        cutoffField.val(elemData[selectedName]["cutoff"]);
    } else {
        nameField.val("");
        detailsField.val("");
        threatField.val("");
        threatLevelField.val("");
        howToTieUpField.val("");
        cutoffField.val("");
    }
})
