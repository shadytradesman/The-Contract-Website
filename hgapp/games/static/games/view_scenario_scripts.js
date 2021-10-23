$(document).ready(function(){
    if (showSpoilers) {
        $('#spoilerModal').modal({});
    }
});

function spoilersAccepted() {
    if (scenarioIsPublic) {
        $("#scenario-content").show();
        $("#spoil-confirm-buttons").hide();
        $('#spoilerModal').modal('hide');
    } else {
        window.location.reload(true);
    }
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