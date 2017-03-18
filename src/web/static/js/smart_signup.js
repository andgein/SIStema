$(document).ready(function () {
    var $container = $('#similar_account_container');
    var $accounts_data = $container.find('.accounts');
    var url = $container.attr('data-url');
    var $form = $('form');
    var $signup_button = $('#signup_button');
    var $decline_button = $('#decline_similar_accounts_button');
    var $close_button = $('#close_similar_accounts');
    var declined_accounts = {};
    var showed_accounts = [];
    var not_declined_count = 0;

    $container.css({
        position: "fixed",
        marginLeft: 0, marginTop: 0,
        top: 0, left: 0,
        zIndex: 100,
        backgroundColor: "orange"
    });

    function close_container() {
       $container.addClass('closed');
    }

    function expand_container() {
       $container.removeClass('closed');
    }

    $close_button.click(function() {
       $container.toggleClass('closed');
    });

    $decline_button.click(function () {
        for (var i = 0; i < showed_accounts.length; ++i) {
            declined_accounts[showed_accounts[i]] = 1;
        }
        not_declined_count = 0;
        $signup_button.removeAttr("disabled");
        $decline_button.hide();
        $close_button.show();
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
            $signup_button.removeAttr("disabled");
            $container.hide();
        } else {
            showed_accounts = Object.keys(data);
            $accounts_data.html(Object.values(data).join());
            if (not_declined_count == 0) {
                $signup_button.removeAttr("disabled");
                $close_button.show();
                $decline_button.hide();
                close_container();
            } else {
                $signup_button.attr("disabled", true);
                $close_button.hide();
                $decline_button.show();
                expand_container();
            }
            $container.show();
        }
    }

    function update_similar_accounts() {
        $.post(url, $form.serializeArray())
            .done(function (data) {
                show_similar_accounts(data);
            })
            .fail(function () {
                alert("error");
            });
    }

    update_similar_accounts();
    $('input:radio').change(update_similar_accounts);
    $('input').focus(function(ev){
        var input = ev.target;
        input.last_focus_value = input.value;
    }).blur(function (ev) {
        var input = ev.target;
        if (input.last_focus_value != input.value) {
            update_similar_accounts();
        }
    });
    $(':input[name$=poldnev_person]').change(update_similar_accounts);
});
