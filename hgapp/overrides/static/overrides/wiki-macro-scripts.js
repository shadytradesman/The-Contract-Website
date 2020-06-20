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
