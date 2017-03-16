$(document).ready(function(){
    $('.entrance-timeline__block.done .entrance-timeline__block__header').click(function(e){
        if ($(e.target).closest('a,button').length > 0)
            return;

        var $block = $(this).closest('.entrance-timeline__block');
        $block.toggleClass('open');
        var $collapseIcon = $block.find('.collapse-icon .fa');
        $collapseIcon.toggleClass('fa-chevron-down fa-chevron-up');
    });
});
