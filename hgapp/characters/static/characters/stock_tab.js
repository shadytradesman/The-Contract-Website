$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip({
        trigger : 'hover'
    });
});

// Equipment
var equipmentValue = JSON.parse(document.getElementById('equipment').textContent);
$($("#js-equipment-form").children("textarea").val(equipmentValue));
$(document).on("click", "#js-edit-equipment-button", function(){
    $("#js-equipment-display").css("display","none");
    $("#js-equipment-form").css("display","block");
});

$("#equipment-form").submit(function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-post-url"),
        data: serializedData,
        success: function (response) {
            var instance = response["equipment"];
            var conv = new showdown.Converter();
            $("#js-equipment-form").children("textarea").val(instance);
            // This is safe only because the only people to see this output are the ones who submitted it.
            $("#js-equipment-text").html(conv.makeHtml(instance));
            $("#js-equipment-display").css("display","block");
            $("#js-equipment-form").css("display","none");
        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})

function resetPopoverContents() {
    $('.js-popover-button').each(function(){
        let content = $(this).parent().nextAll(".js-popover-content").first().html()
        $(this).popover({
            "content": content,
            "html": true,
            "sanitize": false
        });
    })
}
$(resetPopoverContents());


// use consumable submit


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

