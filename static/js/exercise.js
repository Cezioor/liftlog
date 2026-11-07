// Exercise page: start/end photos. Tap to switch; "Animate" alternates every second.
(function () {
  "use strict";

  const figure = document.querySelector("[data-photos]");
  if (!figure) return;
  const images = figure.querySelectorAll("img");
  const caption = figure.querySelector("[data-photo-caption]");
  const playButton = figure.querySelector("[data-photo-play]");
  if (images.length < 2) return;
  // Texts in the page's language (data-text-* in exercise_detail.html).
  const texts = (caption && caption.parentElement.dataset) || {};
  const text = {
    start: texts.textStart || "Start position",
    end: texts.textEnd || "End position",
    animate: texts.textAnimate || "Animate",
    pause: texts.textPause || "Pause",
  };

  let current = 0;
  let timer = null;

  function show(index) {
    current = index % images.length;
    images.forEach(function (img, i) {
      img.hidden = i !== current;
    });
    if (caption) caption.textContent = current === 0 ? text.start : text.end;
  }

  function setPlaying(playing) {
    clearInterval(timer);
    timer = playing ? setInterval(function () { show(current + 1); }, 1000) : null;
    if (playButton) {
      playButton.textContent = playing ? text.pause : text.animate;
      playButton.setAttribute("aria-pressed", playing ? "true" : "false");
    }
  }

  figure.querySelector("[data-photo-toggle]").addEventListener("click", function () {
    setPlaying(false); // a tap means "let me look", so stop the animation
    show(current + 1);
  });
  if (playButton) {
    playButton.addEventListener("click", function () {
      setPlaying(timer === null);
    });
  }

  // Animate by default, unless the phone asks for less motion.
  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  setPlaying(!reduceMotion);
})();
