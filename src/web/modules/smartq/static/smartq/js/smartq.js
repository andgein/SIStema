// TODO(Artem Tabolin): Save answer after timeout if the value was changed
$(document).ready(function() {
  function saveAnswer(url, generated_question_id) {
    var data = {};
    $('input[data-smartq-id=' + generated_question_id + ']').each(function(i) {
      var $self = $(this);
      data[$self.attr('name')] = $self.val();
    });
    $.post(url, data)
  };

  var $inputs = $('input[data-smartq-id]');

  $inputs.focus(function() {
    var $self = $(this);
    $self.data('last_focus_value', $self.val());
  }).blur(function() {
    var $self = $(this);
    if ($self.data('last_focus_value') !== $self.val()) {
      var url = $self.attr('data-smartq-save-url');
      var id = $self.attr('data-smartq-id');

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
    var $self = $(this);
    var rules = {};
    var messages = {};

    $self.find('input[data-smartq-id]').each(function() {
      var $self = $(this);
      var name = $self.attr('name');

      rules[name] = rules[name] || {};
      messages[name] = messages[name] || {};
      
      var regexp = $self.attr('data-smartq-validation-regexp');
      if (regexp) {
        rules[name]['regexp'] = regexp;
      }

      var regexp_message =
        $(this).attr('data-smartq-validation-regexp-message');
      if (regexp_message) {
        messages[name]['regexp'] = regexp_message;
      }
    });

    $self.validate({
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
      },

      errorPlacement: function(error, element) {
        // TODO(Artem Tabolin): show errors in popovers
        //if (element.is(":radio") || element.is(":checkbox")) {
          //element.closest('.option-group').after(error);
        //} else {
          //error.insertAfter(element.parent());
        //}
      }
    });
  };

  $('input[data-smartq-id]').closest('form').each(validateForm);
  
});
