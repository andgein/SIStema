$(document).ready(function(){
    // TODO: trigger only after one second
    // http://stackoverflow.com/questions/14042193/how-to-trigger-an-event-in-input-text-after-i-stop-typing-writing
    $('.entrance-exam__task.entrance-exam__task__test').on('input', function(){
        var $this = $(this);
        var $status = $(this).find('.status');
        var $input = $this.find('input');

        $status.text('Сохранение..');

        var submit_url = $this.data('submit-url');
        var solution = $input.val()
        $.post(submit_url, {
            'solution': solution
        }, function (data) {
            if (data.status != 'ok') {
                $input.removeClass('state-success').addClass('state-error');
                $status.text(data.errors['solution'].join(', ')).removeClass('state-success').addClass('state-error');
            } else {
                $input.removeClass('state-error').addClass('state-success');
                $status.text('Ответ сохранён').removeClass('state-error').addClass('state-success');
            }
        },
        'json')
    });

    $('.entrance-exam__task.entrance-exam__task__file').each(function(){
        var $this = $(this);
        var $status = $this.find('.status');
        var $form = $this.find('form');
        var $input = $form.find('input');

        var submit_url = $this.data('submit-url');
        $form.ajaxForm({
            url: submit_url,
            dataType: 'json',
            beforeSubmit: function () {
                $status.text('Отправка решения..');
            },
            success: function (data) {
                // TODO: copy-paste :(
                if (data.status != 'ok') {
                    $input.removeClass('state-success').addClass('state-error');
                    $status.text(data.errors['solution'].join(', ')).removeClass('state-success').addClass('state-error');
                } else {
                    $input.removeClass('state-error').addClass('state-success');
                    $status.text('Решение загружено, оно будет проверено после окончания вступительной работы').removeClass('state-error').addClass('state-success');
                }
            },
            error: function (data) {
                // TODO
            }
        });

        $input.on('change', function(){
            $form.submit();
        });
    });

    $('.entrance-exam__task.entrance-exam__task__program').each(function(){
        var $this = $(this);
        var $status = $this.find('.status');
        var $form = $this.find('form');

        var submit_url = $this.data('submit-url');
        $form.ajaxForm({
            url: submit_url,
            dataType: 'json',
            beforeSubmit: function () {
                $status.text('Отправка решения..');
            },
            success: function (data) {
                // TODO: copy-paste :(
                if (data.status != 'ok') {
                    //$input.removeClass('state-success').addClass('state-error');
                    $status.text(data.errors['solution'].join(', ')).removeClass('state-success').addClass('state-error');
                } else {
                    //$input.removeClass('state-error').addClass('state-success');
                    $status.text('Решение загружено и сейчас будет проверено').removeClass('state-error').addClass('state-success');
                    window.location.reload();
                }
            },
            error: function (data) {
                // TODO
            }
        });
    });
});