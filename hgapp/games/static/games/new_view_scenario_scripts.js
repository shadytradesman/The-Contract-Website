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

/* Populate the index and create links */
$(function(){
    $(".js-toc-section").each(function() {
        var section = $(this);
        let contentsId = section.data("toc-contents");
        let contents = $("#" + contentsId);
        let headers = contents.find("h1, h2, h3, h4, h5");
        let innerList = section.next("ol");
        for (var i = 0; i < headers.length; i++) {
            let currentHeader = $(headers[i]);
            let headerText = currentHeader.text().substring(0, 40);
            if (headerText.trim().length == 0) {
                continue;
            }
            let headerId = "js-header-" + contentsId + i.toString();
            currentHeader.before('<div id="' + headerId + '" class="css-guide-section"></div>')
            innerList.append('<li role="presentation" class="css-li-' + currentHeader.prop('nodeName') + '"><a href="#' + headerId + '">' + headerText + '</a></li>');
            console.log(headers[i]);
        }
        console.log(contents);
    });
    $('body').scrollspy({ target: '#js-guide-index' });
    $('body').each(function () {
        var $spy = $(this).scrollspy('refresh')
    });
    $(".guide-toc a").on("click", function() {
        const index = $("#js-guide-index");
        const horizontalTocClass = "horizontal-toc";
        index.addClass(horizontalTocClass);
        $(document.body).removeClass("noscroll");
        scrollToc();
    })
});
