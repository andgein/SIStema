$(document).ready(function(){
    var $messages = $('.notification-messages .notification-message');
    $messages.each(function(){
        var $message = $(this);

        var noteStyle = $message.data('note-style');
        var noteShadow = $message.data('note-shadow');
        var noteOpacity = $message.data('note-opacity') || '1';
        var width = '400px';
        var delay = 4000; // 4 seconds

        new PNotify({
            title: '',
            text: $message.text(),
            shadow: noteShadow,
            opacity: noteOpacity,
            type: noteStyle,
            stack: {
                'dir1': 'down',
                'dir2': 'left',
                'push': 'top',
                'spacing1': 10,
                'spacing2': 10,
            },
            width: width,
            delay: delay,
        });
    });
});
