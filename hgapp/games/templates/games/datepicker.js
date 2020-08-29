.input-group-addon <script>
  $(document).ready(function(){
    $("#id_scheduled_start_time_pickers:has(input:not([readonly],[disabled]))").datetimepicker(
    {% if form.default_date %}
        {defaultDate:new Date("{{form.default_date}}")}
    {% endif %}
    );
    $("#id_general-occurred_time_pickers:has(input:not([readonly],[disabled]))").datetimepicker(
    {% if form.default_date %}
        {defaultDate:new Date("{{form.default_date}}")}
    {% endif %}
    );
  });
</script>