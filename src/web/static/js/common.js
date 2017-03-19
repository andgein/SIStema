/* Plugin initializers */
$(document).ready(function() {
    $('.datetimepicker').each(function(_, datetimepicker) {
        var $datetimepicker = $(datetimepicker);
        var format = $datetimepicker.data('format') || 'DD.MM.YYYY';
        var view_mode = $datetimepicker.data('view-mode') || 'days';
        var pick_time = ($datetimepicker.data('pick-time') || 'true') === 'true';

        /* TODO: minDate and maxDate */
        $datetimepicker.datetimepicker({
            format: format,
            viewMode: view_mode,
            pickTime: false
        })
    })
});

$(document).ready(function() {
    $(':input[name$=poldnev_person]').change(function() {
        var text = $(this).data().select2.$selection.text();
        var is_deletion = !text.includes('<span');
        var $val = $($.parseHTML('<span>' + text + '</span>')[0]);
        var field_names = ['last_name', 'first_name', 'middle_name'];
        for (var i = 0; i < field_names.length; i++) {
            var input = $(':input[name$=' + field_names[i] + ']');
            if (is_deletion) {
                input.val(input[0].backup_value).trigger('change');
            } else {
                input[0].backup_value = input.val();
                var field_value = $val.find('.' + field_names[i]).text();
                input.val(field_value).trigger('change');
            }
        }
    });
});
