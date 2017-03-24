/* Enclose links with post-request-link css class*/
$(document).ready(function() {
    $('.post-request-link[href]').click(function(e) {
      var $this = $(this);
      e.stopPropagation();
      e.preventDefault();

      var $form = $('<form>');
      $form.attr('method', 'POST').attr('action', $this.attr('href')).hide();
      $('<input>').attr('type', 'hidden')
                  .attr('name', 'csrfmiddlewaretoken')
                  .attr('value', Cookies.get('csrftoken'))
                  .appendTo($form);
      $form.appendTo('body').submit();
    });
});
