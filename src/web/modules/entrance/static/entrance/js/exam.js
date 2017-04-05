$(document).ready(function(){
    var current_task_id = 0;

    var changeActiveTask = function(task_id) {
        var $link = $('.entrance-exam .nav li a[data-task-id="' + task_id + '"]');
        var $pane = $('.entrance-exam .tab-content .tab-pane[data-task-id="' + task_id + '"]');
        $('.entrance-exam .nav li').removeClass('active');
        $('.entrance-exam .tab-content .tab-pane').removeClass('active');
        $link.closest('li').addClass('active');
        $pane.addClass('active');

        current_task_id = task_id;
    };

    $(window).on('popstate', function(e){
        var task_id = e.originalEvent.state['task_id'];
        changeActiveTask(task_id);
    });

    /* Find currently selected task, set current_task_id and change url if needed */
    var $current_link = $('.entrance-exam .nav li.active a');
    var task_id = $current_link.data('taskId');
    var task_url = $current_link.attr('href');
    current_task_id = task_id;
    history.replaceState({'task_id': task_id}, '', task_url);
    
    var markTaskAsSolved = function (task_id) {
        var $task_link = $('.entrance-exam .nav li a[data-task-id="' + task_id + '"]');
        $task_link.addClass('solved').removeClass('not-solved');
    };

    var updateUpgradePanel = function (){
        var $panel = $('.entrance-exam__upgrade-panel');
        var url = $panel.data('updateUrl');
        $.get(url).done(function(data){
            $panel.html(data);
        });
    };

    var updateProgramSolutions = function(task_id, $block, counter) {
        if (counter > 500) {
            alert('Произошла ошибка при обновлении статуса. Обновите страницу');
            return;
        }

        var $submits = $block.find('.entrance-exam__task__program__submits');
        var url = $block.data('solutionsUrl');
        var content = $submits.html();
        $.get(url)
            .done(function(data){
                if (content != data)
                    $submits.html(data);

                var is_checking = $submits.find('[name="is_checking"]').val();
                if (is_checking == 'true') {
                    setTimeout(function () {
                        updateProgramSolutions(task_id, $block, counter + 1);
                    }, 1000);
                }
                var is_passed = $submits.find('[name="is_passed"]').val();
                if (is_passed == 'true') {
                    markTaskAsSolved(task_id);
                    updateUpgradePanel();
                }
            }).error(function(){
                alert('Произошла ошибка при обновлении статуса. Обновите страницу');
            });
    };

    var initTasksControls = function() {
        $('.entrance-exam .nav li a').click(function(){
            var $this = $(this);
            var task_id = $this.data('taskId');
            var task_url = $this.attr('href');

            history.pushState({'task_id': task_id}, '', task_url);
            changeActiveTask(task_id);
        });

        $('.entrance-exam__task.entrance-exam__task__test input').donetyping(function () {
            var $input = $(this);
            var $this = $input.closest('.entrance-exam__task__test');
            var $status = $this.find('.status');
            var task_id = current_task_id;

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
                        $status.text('Ответ сохранён, он будет проверен после окончания вступительной работы').removeClass('state-error').addClass('state-success');
                        markTaskAsSolved(task_id);
                    }
                },
                'json')
        });

        $('.entrance-exam__task.entrance-exam__task__file').each(function () {
            var $this = $(this);
            var $form = $this.find('form');
            var $status = $form.find('.status');
            var $input = $form.find('input');

            var submitUrl = $this.data('submitUrl');
            $form.ajaxForm({
                url: submitUrl,
                dataType: 'json',
                beforeSubmit: function () {
                    $form[0].reset();
                    $status.text('Отправляю решение...');
                },
                success: function (data) {
                    // TODO: copy-paste :(
                    if (data.status != 'ok') {
                        $input.removeClass('state-success').addClass('state-error');
                        $status.text(data.errors['solution'].join(', ')).removeClass('state-success').addClass('state-error');
                    } else {

                        $input.removeClass('state-error').addClass('state-success');
                        $status.text('Решение загружено, оно будет проверено после окончания вступительной работы')
                            .removeClass('state-error').addClass('state-success')
                            .delay(2000).fadeOut('fast');

                        var $submits = $this.find('.entrance-exam__task__file__submits');
                        var url = $this.data('solutionsUrl');
                        $.get(url).done(function(data){
                            $submits.html(data);
                        });

                        /* TODO (andgein). Potentially bug: if user changed active tab before file has been uploaded */
                        markTaskAsSolved(current_task_id);
                    }
                },
                error: function () {
                    $status.text('Произошла ошибка, попробуйте ещё раз').removeClass('state-success').addClass('state-error');
                }
            });

            $input.on('change', function () {
                $form.submit();
            });
        });

        $('.entrance-exam__task.entrance-exam__task__program')
            .add('.entrance-exam__task.entrance-exam__task__output-only')
            .each(function () {
            var $this = $(this);
            var $status = $this.find('.status');
            var $form = $this.find('form');

            var submitUrl = $this.data('submitUrl');
            $form.ajaxForm({
                url: submitUrl,
                dataType: 'json',
                beforeSubmit: function () {
                    $form[0].reset();
                    $status.text('Отправка решения..');
                },
                success: function (data) {
                    // TODO: copy-paste :(
                    if (data.status != 'ok') {
                        $status.text(data.errors['solution'].join(', ')).removeClass('state-success').addClass('state-error');
                    } else {
                        $status.html('Решение загружено<br />Результаты автоматической проверки появятся справа без&nbsp;обновления страницы').removeClass('state-error').addClass('state-success');
                        $status.delay(3000).fadeOut('fast');
                        /* TODO (andgein). Potentially bug: if user changed active tab before file has been uploaded */
                        updateProgramSolutions(current_task_id, $this, 0);
                    }
                },
                error: function (data) {
                    // TODO
                }
            });
        });
    };

    initTasksControls();
});