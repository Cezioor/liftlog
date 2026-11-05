// Forms marked data-submit-once: after the first tap the button is disabled and says
// what is happening. Signing up takes a few seconds on the free server (password
// hashing); a second tap used to send the form twice, and the second copy failed with
// "a user with that username already exists".
(function () {
  "use strict";
  document.addEventListener("submit", function (event) {
    const form = event.target;
    if (!form.matches("form[data-submit-once]")) return;
    if (form.dataset.submitting) {
      event.preventDefault();
      return;
    }
    form.dataset.submitting = "1";
    const button = event.submitter || form.querySelector("button[type=submit]");
    if (button) {
      // Disable on the next tick: disabling right away would drop the button's own
      // name/value from the data being sent.
      setTimeout(function () {
        button.disabled = true;
        if (button.dataset.busyText) button.textContent = button.dataset.busyText;
      }, 0);
    }
  });
  // Back/forward cache: a page restored after navigating away must be usable again.
  window.addEventListener("pageshow", function (event) {
    if (!event.persisted) return;
    document.querySelectorAll("form[data-submitting]").forEach(function (form) {
      delete form.dataset.submitting;
      form.querySelectorAll("button[disabled]").forEach(function (b) {
        b.disabled = false;
      });
    });
  });
})();
