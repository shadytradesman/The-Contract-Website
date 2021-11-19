$(document).ready(function(){
    $("input[id$=-MVP]").change(function () {
         $("input[id$=-MVP]").each(function () {
             this.checked = false;
         })
         this.checked = true;
    });
    $("input[id$=-MVP]")[0].checked = true;
})
