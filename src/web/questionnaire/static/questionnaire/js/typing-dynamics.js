$(document).ready(function() {
    var inputName = 'typing-dynamics-typing_data';
    var typingData = {};

    $('[name=' + inputName + ']').each(function(i, input) {
        var $input = $(input);
        var $form = $input.closest('form');
        $form.find('[type=text], textarea').keyup(function(e) {
            var name = $(this).attr('name');
            typingData[name] = typingData[name] || [];
            typingData[name].push({
                type: 'keyup',
                timestamp_ms: Date.now(),
            });
        }).keydown(function(e) {
            var name = $(this).attr('name');
            typingData[name] = typingData[name] || [];
            typingData[name].push({
                type: 'keydown',
                timestamp_ms: Date.now(),
            });
        });
        $form.submit(function() {
          $input.val(JSON.stringify({data: typingData}));
          return true;
        });
    });
});
