// add world element
$(".js-world-element-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var delUrl = $(this).attr("data-delete-world-element-url");
    var editUrl = $(this).attr("data-edit-world-element-url");
    var elementContainer = $(this).closest(".js-world-element-container");
    var form = $(this);

    $.ajax({
        type: 'POST',
        url: $(this).attr("data-new-world-element-url"),
        data: serializedData,
        success: function (response) {
            form.trigger('reset');
            var instance = JSON.parse(response["instance"]);
            var fields = instance[0]["fields"];
            delUrl = delUrl.replace(/worldElementIdJs/g, JSON.parse(response["id"]));
            editUrl = editUrl.replace(/worldElementIdJs/g, JSON.parse(response["id"]));
            var tmplMarkup = $('#world-entity-template').html();
            var compiledTmpl = tmplMarkup.replace(/__world_entity_description__/g, fields["description"||""]);
            var compiledTmpl = compiledTmpl.replace(/__world_entity_name__/g, fields["name"||""]);
            var compiledTmpl = compiledTmpl.replace(/__world_entity_system__/g, fields["system"||""]);
            var compiledTmpl = compiledTmpl.replace(/__delUrl__/g, delUrl);
            var compiledTmpl = compiledTmpl.replace(/__editUrl__/g, editUrl);
            var newContentContainer = elementContainer.find(".js-world-element-content-" + response["cellId"]);
            newContentContainer.append(compiledTmpl);
            newContentContainer.prev().show();
            newContentContainer.parent().show();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

// delete world-element
$(".js-world-element-container").on("submit",".js-delete-world-element-form", function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var worldElement = $(this);
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-del-world-element-url"),
        data: serializedData,
        success: function (response) {
            worldElement.closest(".js-world-element-delete").remove();
            worldElement.parent().parent().remove();
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

// edit world element form expand
$(document).on("click", ".js-edit-world-element-button", function(){
    $(this).parent().hide();
    $(this).parent().nextAll(".css-world-element-delete").first().hide();
    let valElement = $(this).parent().nextAll(".css-world-entity-value").first();
    let formElement = $(this).parent().nextAll(".js-edit-world-element-form").first();
    valElement.hide();
    formElement.show();
    formElement.find("#id_name").val(valElement.find(".css-world-element-name").text().trim());
    formElement.find("#id_description").val(valElement.find(".css-world-element-description").text().trim());
    formElement.find("#id_system").val(valElement.find(".css-world-element-system").text().trim());
});


// edit world element form submit
$(".js-world-element-container").on("submit",".js-edit-world-element-form", function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    var worldElement = $(this);
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-edit-world-element-url"),
        data: serializedData,
        success: function (response) {
            worldElement.prevAll(".css-world-element-delete").first().show();
            worldElement.prevAll(".css-world-element-edit").first().show();
            let valElement = worldElement.prevAll(".css-world-entity-value").first();
            let formElement = worldElement;
            valElement.show();
            formElement.hide();
            var instance = JSON.parse(response["instance"]);
            var fields = instance[0]["fields"];
            valElement.find(".css-world-element-name").text(fields["name"||""])
            valElement.find(".css-world-element-description").text(fields["description"||""])
            valElement.find(".css-world-element-system").text(fields["system"||""])
            let greyOut = response["grey_out"];
            let artifactStatus = response["artifact_status"];
            if (null != greyOut) {
                if (greyOut) {
                    valElement.parent().addClass("css-sig-item-greyed-out");
                } else {
                    valElement.parent().removeClass("css-sig-item-greyed-out");
                }
            }
            if (null!= artifactStatus) {
                let statusSelector = valElement.parent().find(".js-item-availability-change");
                statusSelector.find('option').remove();
                statusSelector.append('<option value="">No change</option>');
                if (artifactStatus === "LOST") {
                    statusSelector.append('<option value="RECOVERED">Recovered</option>');
                    valElement.find(".css-reason-unavail").text("Currently Lost.");
                } else if (artifactStatus === "DESTROYED") {
                    statusSelector.append('<option value="REPAIRED">Repaired</option>');
                    valElement.find(".css-reason-unavail").text("Currently Destroyed.");
                }
                else {
                    statusSelector.append('<option value="DESTROYED">Destroyed</option>');
                    statusSelector.append('<option value="LOST">Lost</option>');
                    valElement.find(".css-reason-unavail").text("");
                }
            }
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})


$(function(){
    function handleAvailabilityChange() {
        const status = $(this).val();
        if (status === "") {
            $(this).parent().parent().parent().next().hide();
        } else {
            $(this).parent().parent().parent().next().show();
        }
    }
    $(".js-item-availability-change").change(handleAvailabilityChange);
});


// transfer artifact expand
$(document).on("click", ".js-transfer-artifact-button", function(){
    $(this).parent().hide();
    let formElement = $(this).parent().nextAll(".js-transfer-artifact-form").first();
    formElement.show();
});

// use consumable submit
$(".css-consumable-item").on("submit",".js-use-consumable-form", function (e) {
    e.preventDefault();
    let form = $(this);
    let popover = form.parent().parent().parent().children(".js-popover-button");
    $(".js-consumable-use-submit").disabled=true;
    let artId = $(this).attr("data-artifact-id");
    let newQuantity = parseInt(popover.attr("data-rem-quantity"));
    console.log(newQuantity);
    $(this).children("input[name='new_quantity']").val(newQuantity);
    console.log($(this));
    var serializedData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-url"),
        data: serializedData,
        success: function (response) {
            let resultingQuantity = response["new_quantity"];
            $(".js-consumable-quantity-"+artId).text(resultingQuantity);
            $(".js-consumable-minus-quantity-"+artId).text(resultingQuantity-1);
            popover.popover('hide');
            $(".js-consumable-use-submit").disabled=false;
            popover.attr("data-rem-quantity", resultingQuantity-1);
            if (resultingQuantity === 0) {
                popover.parent().parent().hide();
                popover.closest(".js-world-element-delete").addClass("css-sig-item-greyed-out");
                popover.parent().parent().parent().find(".js-consumable-delete-container").show();
            }
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

