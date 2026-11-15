(function () {
  'use strict';

  /* Ask before destructive actions: <form data-confirm="Are you sure?"> */
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  /* Show the chosen photo before it is uploaded. */
  document.querySelectorAll('input[type="file"][data-preview]').forEach(function (input) {
    var preview = input.closest('form').querySelector('.preview');
    if (!preview) return;
    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file) {
        preview.hidden = true;
        return;
      }
      preview.src = URL.createObjectURL(file);
      preview.hidden = false;
    });
  });
})();
