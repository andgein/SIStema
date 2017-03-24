// TODO(Artem Tabolin): Save answer after timeout if the value was changed
$(document).ready(function() {
  function saveAnswer(url, generated_question_id) {
    var data = {};
    $('input[data-smartq-id=' + generated_question_id + ']').each(function(i) {
      var $this = $(this);
      data[$this.attr('name')] = $this.val();
    });
    $.post(url, data)
  };

  var $inputs = $('input[data-smartq-id]');

  $inputs.focus(function() {
    var $this = $(this);
    $this.data('last_focus_value', $this.val());
  }).blur(function() {
    var $this = $(this);
    if ($this.data('last_focus_value') !== $this.val()) {
      var url = $this.attr('data-smartq-save-url');
      var id = $this.attr('data-smartq-id');

      saveAnswer(url, id);
    }
  });
});

// Validation
$(document).ready(function() {
  $.validator.addMethod(
      "regexp",
      function(value, element, regexp) {
        var re = new RegExp(regexp);
        return this.optional(element) || re.test(value);
      },
      "Please check your input."
  );

  function validateForm() {
    var $this = $(this);
    var rules = {};
    var messages = {};

    $this.find('input[data-smartq-id]').each(function() {
      var $this = $(this);
      var name = $this.attr('name');

      rules[name] = rules[name] || {};
      messages[name] = messages[name] || {};
      
      var regexp = $this.attr('data-smartq-validation-regexp');
      if (regexp) {
        rules[name]['regexp'] = regexp;
      }

      messages[name]['required'] = 'Это поле необходимо заполнить';

      var regexp_message =
        $this.attr('data-smartq-validation-regexp-message');
      if (regexp_message) {
        messages[name]['regexp'] = regexp_message;
      }
    }).focus(function() {
      $(this).popover('show');
    }).blur(function() {
      $(this).popover('hide');
    });

    $this.validate({
      errorClass: 'state-error',
      validClass: 'state-success-do-not-highlight',
      errorElement: 'em',
      rules: rules,
      messages: messages,

      highlight: function(element, errorClass, validClass) {
        $(element).closest('.field').addClass(errorClass)
                                    .removeClass(validClass);
      },

      unhighlight: function(element, errorClass, validClass) {
        $(element).closest('.field').removeClass(errorClass)
                                    .addClass(validClass);
        $(element).popover('destroy');
      },

      errorPlacement: function(error, element) {
        var $element = $(element);
        $element.popover('destroy').popover({
          trigger: 'manual',
          placement: 'top',
          content: error,
          html: true,
        });
        if ($element.is(':focus')) {
          $element.popover('show');
        }
      }
    });
  };

  $('input[data-smartq-id]').closest('form').each(validateForm);
  
});
