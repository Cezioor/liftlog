// Exercise picker: rows of filter chips scroll sideways. After a refresh (the chips come
// back with the results) each row keeps where it was scrolled to; on a page load, and
// whenever the chosen chip is out of sight, the row scrolls so that chip is visible.
(function () {
  "use strict";

  let saved = {};

  function rows() {
    return document.querySelectorAll("[data-chip-row]");
  }

  function revealChosen(row) {
    const input = row.querySelector("input:checked");
    if (!input || !input.value) return; // "All …" is the first chip anyway
    const chip = input.closest(".chip");
    const rowBox = row.getBoundingClientRect();
    const chipBox = chip.getBoundingClientRect();
    if (chipBox.left < rowBox.left || chipBox.right > rowBox.right) {
      row.scrollLeft += chipBox.left - rowBox.left - 16;
    }
  }

  function remember() {
    saved = {};
    rows().forEach(function (row) {
      saved[row.dataset.chipRow] = row.scrollLeft;
    });
  }

  function restore() {
    rows().forEach(function (row) {
      if (row.dataset.chipRow in saved) row.scrollLeft = saved[row.dataset.chipRow];
      revealChosen(row);
    });
  }

  rows().forEach(revealChosen);
  // The out-of-band chips are swapped before the results, so both events cover them.
  document.addEventListener("htmx:beforeSwap", remember);
  document.addEventListener("htmx:afterSwap", restore);
})();
