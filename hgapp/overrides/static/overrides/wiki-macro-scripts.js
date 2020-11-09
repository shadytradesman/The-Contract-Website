function setupCollapsibles(element) {
      element.addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "block") {
          content.style.display = "none";
        } else {
          content.style.display = "block";
        }
      });
}

$(function() {
    var elements = document.getElementsByClassName("wiki-entry-collapsible");
    var i;
    for (i = 0; i < elements.length; i++) {
        setupCollapsibles(elements[i]);
    }
});

$(function() {
    var index= $("#js-article-index");
    $("#js-lower-index").html(index.html());
});

function findNextUrl(currentArticle, isPop) {
    if (currentArticle.length) {
        var child = currentArticle.find("ul>li>a");
        if (child.length && !isPop) {
            return child.attr("href");
        }
        var next = currentArticle.next();
        if (next.length) {
            return next.find("a").attr("href");
        }
        var parent = currentArticle.parent("ul").parent("li");
        if (parent.length) {
            return findNextUrl(parent, true);
        } else {
            return null;
        }
    } else {
        return $(".article-toc>li>a").attr("href");
    }
}

function findPrevUrl(currentArticle, isPop) {
    if (currentArticle.length) {
        var previous = currentArticle.prev();
        if (previous.length) {
            var child = previous.children("ul").children("li");
            if (child.length) {
                while( child.length ) {
                    child = child.last().children("ul").children("li");
                }
                return child.end().end().parent().find("a").last().attr("href");
            } else {
                return previous.find("a").attr("href");
            }
        } else {
            var parent = currentArticle.parent("ul").parent("li");
            if (parent.length) {
                return parent.find("a").attr("href");
            }
        }
    }
    return null;
}

function setNavLinks() {
    nextUrl = findNextUrl($("#current-article"), false);
    if (nextUrl) {
        $(".js-next-article").attr("href", nextUrl);
        $(".js-next-article").show();
    }
    previousUrl = findPrevUrl($("#current-article"), false);
    if (previousUrl) {
        $(".js-prev-article").attr("href", previousUrl);
        $(".js-prev-article").show();
    }
}

$(function() {
    setNavLinks();
});