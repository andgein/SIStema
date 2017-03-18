// TODO(Artem Tabolin): Save answer after timeout if the value was changed
$(document).ready(function() {
  function saveAnswer(url, generated_question_id) {
    var data = {};
    $('input[data-smartq-id=' + generated_question_id + ']').each(function(i) {
      data[$(this).attr('name')] = $(this).val();
    });
    $.post(url, data)
  };

  var inputs = $('input[data-smartq-id]');

  inputs.focus(function() {
    $(this).data('last_focus_value', $(this).val());
  }).blur(function() {
    if ($(this).data('last_focus_value') !== $(this).val()) {
      var url = $(this).attr('data-smartq-save-url');
      var id = $(this).attr('data-smartq-id');

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
    var rules = {};
    $(this).find('input[data-smartq-id]').each(function() {
      var name = $(this).attr('name');
      rules[name] = rules[name] || {};
      
      var regexp = $(this).attr('data-smartq-validation-regexp');
      if (regexp) {
        rules[name]['regex'] = regexp;
        rules[name]['required'] = true;
      }

    });

    $(this).validate({
      'rules': rules
    });
  };

  $('input[data-smartq-id]').closest('form').each(validateForm);
  
});
