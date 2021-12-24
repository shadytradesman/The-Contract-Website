const powerBlob = JSON.parse(JSON.parse(document.getElementById('powerBlob').textContent));
var unrenderedSystemText = "";

function addRadiosForComponent(container, component, label) {
        $(container).append(
            $('<input>').prop({
                type: 'radio',
                id: 'radio-' + component.slug,
                data_pk: component.slug,
                name: label,
                value: component.name
            })
        ).append(
            $('<label>').prop({
                for: 'radio-' + component.slug
            }).html(component.name)
        ).append(
            $('<br>')
        );
}

function populatePowerForm(modality, vector, effect) {
	console.log(modality);
	console.log(vector);
	console.log(effect);
	var components = [modality, vector, effect];

	unrenderedSystemText = modality.system + "<br>" + vector.system + "<br>" + effect.system + "<br>";
	$('#unrendered-system').html(unrenderedSystemText);
	let enhancements = new Set();
	let drawbacks = new Set();
	let fields = new Set();
	let bl_enhancements = new Set();
	let bl_drawbacks = new Set();
	let bl_fields = new Set();
	components.forEach(comp => comp.enhancements.forEach(mod => enhancements.add(mod)));
	console.log(enhancements);
}

$(function() {
	Object.values(powerBlob.effects).forEach(comp => addRadiosForComponent("#effects", comp, "effect"));
	Object.values(powerBlob.modalities).forEach(comp => addRadiosForComponent("#modalities", comp, "modalities"));
	Object.values(powerBlob.vectors).forEach(comp => addRadiosForComponent("#vectors", comp, "vectors"));

	$('input').on("click", function(e) {
		checkedEffects = $('input[name="effect"]:checked');
		checkedModalities = $('input[name="modalities"]:checked');
		checkedVectors = $('input[name="vectors"]:checked');
		if (checkedEffects.length && checkedModalities.length && checkedVectors.length) {
			console.log("all three!");
			populatePowerForm(powerBlob.modalities[checkedModalities[0].data_pk],
				powerBlob.vectors[checkedVectors[0].data_pk],
				powerBlob.effects[checkedEffects[0].data_pk]);
		}
	});
});

