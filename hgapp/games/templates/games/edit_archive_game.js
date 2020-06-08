<script>
  $(document).ready(function(){

    var wasRingerLast = [];

    function setRinger(id, isRinger) {
        var select = $("select[id$=" + id + "-outcome]");
        if (wasRingerLast[id] != isRinger) {
            if (isRinger) {
                select.val('RINGER_VICTORY');
            } else {
                select.val('WIN');
            }
        }
        select.children("option[value=RINGER_VICTORY]").prop('disabled', !isRinger);
        select.children("option[value=RINGER_FAILURE]").prop('disabled', !isRinger);
        select.children("option[value=DECLINED]").prop('disabled', isRinger);
        select.children("option[value=DEATH]").prop('disabled', isRinger);
        select.children("option[value=LOSS]").prop('disabled', isRinger);
        select.children("option[value=WIN]").prop('disabled', isRinger);
        wasRingerLast[id] = isRinger;
    }

    $("select[id$=attending_character]").change(function () {
        var regex = ".*([\\d]).*";
        var idString = $(this).attr('id');
        var idNum = idString.toString().match(regex)[1];
        if (this.value == "") {
            setRinger(idNum, true);
        }else{
            setRinger(idNum, false);
        }
    });


    setRinger(0, true);
    setRinger(1, true);
    setRinger(2, true);
    setRinger(3, true);


  });
</script>