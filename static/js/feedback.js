// The "Report" ("Zgłoś") dialog: opens over the current page, sends with HTMX (feedback form),
// shows the thanks and closes by itself. The page underneath, e.g. a workout with
// numbers typed but not logged yet, is never reloaded or touched.
(function () {
  "use strict";

  const dialog = document.getElementById("feedback-dialog");
  if (!dialog || typeof dialog.showModal !== "function") return; // the link opens the page
  const body = dialog.querySelector("[data-feedback-body]");
  const emptyForm = body.innerHTML; // to start fresh next time
  let closeTimer = null;

  function reset() {
    clearTimeout(closeTimer);
    body.innerHTML = emptyForm;
    if (window.htmx) window.htmx.process(body);
    // Report the page the user is on right now (it can change without a reload).
    const page = body.querySelector("input[name='feedback-page']");
    if (page) page.value = location.pathname + location.search;
  }

  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-feedback-open]")) {
      event.preventDefault();
      reset();
      dialog.showModal();
      const text = dialog.querySelector("textarea");
      if (text) text.focus();
    } else if (event.target.closest("[data-feedback-close]")) {
      dialog.close();
    }
  });

  // Tap on the dark backdrop closes it, like other phone dialogs.
  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) dialog.close();
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    if (dialog.contains(event.target) && dialog.querySelector("[data-feedback-done]")) {
      closeTimer = setTimeout(function () {
        dialog.close();
      }, 1800);
    }
  });
})();
