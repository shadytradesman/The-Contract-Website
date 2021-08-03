const abilityValueById = JSON.parse(document.getElementById('abilityValueById').textContent);
const attributeValueById = JSON.parse(document.getElementById('attributeValueById').textContent);

window.onload = function () {
    $(".js-roll-num-dice").each(function(){
        const attrId = parseInt($(this).attr('data-attr-id'));
        const isMind = $(this).attr('data-is-mind');
        const isBody = $(this).attr('data-is-body');
        const attrId2 = parseInt($(this).attr('data-attr2-id'));
        const abilityId = parseInt($(this).attr('data-ability-id'));
        var abilityValue = abilityValueById[abilityId];
        var mindValue = isMind === "True" ? numMindLevels : 0;
        var bodyValue =  isBody === "True" ? numBodyLevels : 0;
        var attrValue = attributeValueById[attrId];
        var attr2Value = attributeValueById[attrId2];
        abilityValue = abilityValue ? abilityValue : 0;
        attrValue = attrValue ? attrValue : 0;
        attr2Value = attr2Value ? attr2Value : 0;
        if (attrId || attrId2 || abilityId || mindValue || bodyValue) {
            $(this).html(abilityValue + attrValue + attr2Value + mindValue + bodyValue);
            $(this).parent().show();
        }
        var difficultyElement = $(this).parent().parent().children(".js-roll-difficulty");
        if (difficultyElement.length == 1) {
            var difficultyValue = parseInt(difficultyElement.attr('data-difficulty'));
            if (abilityValue === 0 && attr2Value === 0 && mindValue === 0 && bodyValue === 0) {
                difficultyElement.html(difficultyValue + "+1 (untrained)");
            } else {
                difficultyElement.html(difficultyValue);
            }
        }
    });
};
