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

// TODO(Artem Tabolin): implement displaying of verification error messages and
//     field highlighting.
// Validation
$(document).ready(function() {
  $.validator.addMethod(
      "regex",
      function(value, element, regexp) {
        var re = new RegExp(regexp);
        return this.optional(element) || re.test(value);
      },
      "Please check your input."
  );

  function validateForm() {
    var $self = $(this);
    var rules = {};
    $self.find('input[data-smartq-id]').each(function() {
      var $self = $(this);
      var name = $self.attr('name');
      rules[name] = rules[name] || {};
      
      var regexp = $self.attr('data-smartq-validation-regexp');
      if (regexp) {
        rules[name]['regex'] = regexp;
        rules[name]['required'] = true;
      }

    });

    $self.validate({
      'rules': rules
    });
  };

  $('input[data-smartq-id]').closest('form').each(validateForm);
  
});
