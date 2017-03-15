$(document).ready(function () {
    var form = $('form');
    function update_similar_accounts() {
        $.post('/accounts/find-similar/', form.serializeArray())
            .done(function (data) {
                console.log(data);
            })
            .fail(function () {
                alert("error");
            });
    }

    update_similar_accounts();
    $('input:radio').change(update_similar_accounts);
    $('input').focus(function(ev){
        var input = ev.target;
        input.last_focus_value = input.value
    }).blur(function (ev) {
        var input = ev.target;
        if (input.last_focus_value != input.value) {
            update_similar_accounts();
        }
    });
});
