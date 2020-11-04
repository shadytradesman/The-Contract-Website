$(document).ready(function(){
    if (scenarioPublic) {
        $('#spoilerModal').modal({});
    }
});

function spoilersAccepted() {
    $("#scenario-content").show();
    $("#spoil-confirm-buttons").hide();
    $('#spoilerModal').modal('hide');
}

// delete battle injury
$(".container").on("submit",".js-accept-spoilers", function (e) {
    e.preventDefault();
    var serializedData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: $(this).attr("data-spoiler-url"),
        data: serializedData,
        success: function (response) {
            spoilersAccepted();

        },
        error: function (response) {
            console.log(response);
            alert(response["responseJSON"]["error"]);
        }
    })
})