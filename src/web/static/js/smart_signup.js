$(document).ready(function () {
    var $container = $('#similar-accounts__popup');
    var $accounts_data = $container.find('.accounts');
    var url = $container.attr('data-url');
    var $form = $('form');
    var $signup_button = $('#signup__button');
    var $decline_button = $('#decline-similar-accounts__button');
    var declined_accounts = {};
    var showed_accounts = [];
    var not_declined_count = 0;

    var open_container = function() {
        $.magnificPopup.open({
            removalDelay: 500, //delay removal by X to allow out-animation,
            items: {
              src: '#' + $container.attr('id')
            },
            callbacks: {
                close: function(){
                    $signup_button.removeAttr('disabled');
                }
            },
            midClick: true // allow opening popup on middle mouse click. Always set it to true if you don't provide alternative source.
        });
    };

    var close_container = function() {
        $.magnificPopup.close()
    };

    $decline_button.click(function () {
        for (var i = 0; i < showed_accounts.length; ++i) {
            declined_accounts[showed_accounts[i]] = 1;
        }
        not_declined_count = 0;
        $signup_button.removeAttr('disabled');
        close_container();
    });

    function show_similar_accounts(data) {
        not_declined_count = 0;
        for (var account_id in data) {
            if (!(account_id in declined_accounts)) {
                not_declined_count++;
            }
        }
        if (data.length == 0) {
            $signup_button.removeAttr('disabled');
            close_container();
        } else {
            showed_accounts = Object.keys(data);
            $accounts_data.html(Object.values(data).join());
            if (not_declined_count == 0) {
                $signup_button.removeAttr('disabled');
                $decline_button.hide();
                close_container();
            } else {
                $signup_button.attr('disabled', true);
                $decline_button.show();
                open_container();
            }
        }
    }

    function update_similar_accounts() {
        $.post(url, $form.serializeArray())
            .done(function (data) {
                show_similar_accounts(data);
            })
            .fail(function () {
                alert('Произошла ошибка. Попробуйте ещё раз. ' +
                    'В случае повторения ошибки напишите нам на lksh@lksh.ru');
            });
    }

    update_similar_accounts();
    $('input:radio').change(update_similar_accounts);
    $('input').focus(function(e){
        var input = e.target;
        input.last_focus_value = input.value;
    }).blur(function (e) {
        var input = e.target;
        if (input.last_focus_value != input.value) {
            update_similar_accounts();
        }
    });
    $(':input[name$=poldnev_person]').change(update_similar_accounts);
});
