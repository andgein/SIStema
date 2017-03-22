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

/* TODO (Andgein) Extract it from common.js */
$(document).ready(function() {
    var field_names = ['last_name', 'first_name', 'middle_name'];

    $(':input[name$=poldnev_person]').on('select2:select', function(e) {
        var text = e.params.data.text;
        var $val = $($.parseHTML('<span>' + text + '</span>'));
        for (var i = 0; i < field_names.length; i++) {
            var $input = $(':input[name$="' + field_names[i] + '"]');
            $input.data('backup-value',  $input.val());
            var field_value = $val.find('.' + field_names[i]).text();
            $input.val(field_value).trigger('change');
        }
    });

    $(':input[name$=poldnev_person]').on('select2:unselect', function(e) {
        for (var i = 0; i < field_names.length; i++) {
            var $input = $(':input[name$="' + field_names[i] + '"]');
            $input.val($input.data('backup-value')).trigger('change');
        }
    });
});
