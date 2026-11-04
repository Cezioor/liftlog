// Workout screen: −/+ steppers and the rest timer.
(function () {
  "use strict";

  // --- Steppers -----------------------------------------------------------
  document.addEventListener("click", function (event) {
    const button = event.target.closest(".step");
    if (!button) return;
    const input = document.getElementById(button.dataset.for);
    if (!input) return;
    const step = parseFloat(button.dataset.step);
    const current = parseFloat((input.value || "0").replace(",", ".")) || 0;
    const next = Math.max(0, Math.round((current + step) * 100) / 100);
    input.value = String(next);
  });

  // --- Rest timer ---------------------------------------------------------
  // The end time is stored (not a countdown), so the timer stays correct after
  // the phone locks, the tab is throttled or the page reloads.
  const STORAGE_KEY = "liftlog.restEndsAt";
  const bar = document.getElementById("rest-timer");
  const timeEl = document.getElementById("rest-time");
  const labelEl = document.getElementById("rest-label");
  const shortcutLink = document.getElementById("rest-shortcut");
  if (!bar) return;

  // Settings rendered by the server (see accounts.models.UserSettings).
  const config = (document.getElementById("workout-config") || {}).dataset || {};
  const soundEnabled = config.restSound === "1";

  let endsAt = null;
  let tick = null;
  let audio = null;

  function store(value) {
    try {
      if (value) localStorage.setItem(STORAGE_KEY, String(value));
      else localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      /* private mode etc.: the timer still works, just not across reloads */
    }
  }

  function format(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m + ":" + String(s).padStart(2, "0");
  }

  function beep() {
    try {
      if (!audio) return;
      const osc = audio.createOscillator();
      const gain = audio.createGain();
      osc.frequency.value = 880;
      gain.gain.value = 0.15;
      osc.connect(gain).connect(audio.destination);
      osc.start();
      osc.stop(audio.currentTime + 0.4);
    } catch (e) {
      /* sound is a nice-to-have */
    }
  }

  function render() {
    if (endsAt === null) return;
    const left = Math.ceil((endsAt - Date.now()) / 1000);
    if (left > 0) {
      timeEl.textContent = format(left);
      return;
    }
    finish();
  }

  function finish() {
    clearInterval(tick);
    endsAt = null;
    store(null);
    labelEl.textContent = "Rest over";
    timeEl.textContent = "Go!";
    bar.classList.add("rest-done");
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
    // Only beep when LiftLog is actually on screen.
    if (soundEnabled && document.visibilityState === "visible") beep();
    setTimeout(hide, 4000);
  }

  function hide() {
    if (endsAt !== null) return; // a new rest started meanwhile
    bar.hidden = true;
    bar.classList.remove("rest-done");
    if (shortcutLink) shortcutLink.hidden = true;
  }

  function start(untilMs) {
    clearInterval(tick);
    endsAt = untilMs;
    store(endsAt);
    labelEl.textContent = "Rest";
    bar.classList.remove("rest-done");
    bar.hidden = false;
    render();
    tick = setInterval(render, 250);
  }

  // The server sends HX-Trigger: {"restStart": {"seconds": N}} after a set is saved.
  document.addEventListener("restStart", function (event) {
    const seconds = (event.detail && event.detail.seconds) || 90;
    start(Date.now() + seconds * 1000);
    // iOS only opens shortcuts:// after a tap, so this is a button, not a redirect.
    if (shortcutLink) {
      const url = event.detail && event.detail.shortcutUrl;
      shortcutLink.hidden = !url;
      if (url) shortcutLink.href = url;
    }
  });

  // Sound needs a user gesture first; create the audio context on the first tap.
  document.addEventListener(
    "pointerdown",
    function () {
      if (!audio && window.AudioContext) audio = new AudioContext();
    },
    { once: true }
  );

  bar.addEventListener("click", function (event) {
    if (event.target.closest("[data-rest-skip]")) {
      clearInterval(tick);
      endsAt = null;
      store(null);
      hide();
    }
    const add = event.target.closest("[data-rest-add]");
    if (add && endsAt !== null) {
      start(endsAt + parseInt(add.dataset.restAdd, 10) * 1000);
    }
  });

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) render();
  });

  // Resume a rest that was running before a reload.
  let saved = null;
  try {
    saved = parseInt(localStorage.getItem(STORAGE_KEY), 10);
  } catch (e) {
    saved = null;
  }
  if (saved && saved > Date.now()) start(saved);
  else store(null);

  // --- Keep the screen on (Screen Wake Lock API) ---------------------------
  // Browsers release the lock whenever the page is hidden, so it is requested
  // again each time the workout screen becomes visible.
  if (config.keepScreenOn === "1") {
    const status = document.getElementById("wake-status");
    const say = function (text) {
      if (!status) return;
      status.textContent = text;
      status.hidden = false;
    };

    if (!("wakeLock" in navigator)) {
      // Not supported, or not HTTPS (wake lock needs a secure connection).
      say("This browser can't keep the screen on. You can set Auto-Lock in the phone's display settings instead.");
    } else {
      let lock = null;
      const acquire = async function () {
        if (document.visibilityState !== "visible" || lock) return;
        try {
          lock = await navigator.wakeLock.request("screen");
          lock.addEventListener("release", function () {
            lock = null;
          });
          say("Screen stays on during this workout.");
        } catch (e) {
          // e.g. Low Power Mode on iPhone, or the browser refused.
          say("Couldn't keep the screen on right now (battery saver?).");
        }
      };
      document.addEventListener("visibilitychange", acquire);
      acquire();
    }
  }
})();
