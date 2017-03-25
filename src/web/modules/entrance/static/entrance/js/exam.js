$(document).ready(function(){
    $('.entrance-exam__task.entrance-exam__task__test input').donetyping(function(){
        var $input = $(this);
        var $this = $input.closest('.entrance-exam__task__test');
        var $status = $this.find('.status');

        $status.text('Сохранение..');

        var submit_url = $this.data('submitUrl');
        var solution = $input.val();
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
        var $form = $this.find('form');
        var $status = $form.find('.status');
        var $input = $form.find('input');

        var submitUrl = $this.data('submitUrl');
        $form.ajaxForm({
            url: submitUrl,
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

    var updateProgramSolutions = function($block, counter) {
        if (counter > 100) {
            alert('Произошла ошибка при обновлении статуса. Обновите страницу');
            return;
        }

        var $submits = $block.find('.entrance-exam__task__program__submits');
        var url = $block.data('programSolutionsUrl');
        var content = $submits.html();
        $.get(url)
            .done(function(data){
                if (content != data)
                    $submits.html(data);

                var is_checking = $submits.find('[name="is_checking"]').val();
                if (is_checking == 'true') {
                    setTimeout(function () {
                        updateProgramSolutions($block);
                    }, 1000);
                }
            }).error(function(){
                alert('Произошла ошибка при обновлении статуса. Обновите страницу');
            });
    };

    $('.entrance-exam__task.entrance-exam__task__program').each(function(){
        var $this = $(this);
        var $status = $this.find('.status');
        var $form = $this.find('form');

        var submitUrl = $this.data('submitUrl');
        $form.ajaxForm({
            url: submitUrl,
            dataType: 'json',
            beforeSubmit: function () {
                $status.text('Отправка решения..');
            },
            success: function (data) {
                // TODO: copy-paste :(
                if (data.status != 'ok') {
                    $status.text(data.errors['solution'].join(', ')).removeClass('state-success').addClass('state-error');
                } else {
                    $status.text('Решение загружено и сейчас будет проверено').removeClass('state-error').addClass('state-success');
                    $status.delay(3000).fadeOut('fast');

                    updateProgramSolutions($this, 0);
                }
            },
            error: function (data) {
                // TODO
            }
        });
    });
});