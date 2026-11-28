/* Password Strength Checker front-end.
 * Privacy: the password is only held in the input field and sent once in the
 * POST body to /api/check. It is never put in a URL, localStorage,
 * sessionStorage, cookies or the console. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var input = $("password"), toggle = $("toggle"), btn = $("check-btn");
  var errorBox = $("error"), result = $("result");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var requestId = 0;

  function slug(label) { return label.toLowerCase().replace(/\s+/g, "-"); }

  function setBusy(busy) {
    btn.disabled = busy;
    btn.classList.toggle("is-loading", busy);
    btn.setAttribute("aria-busy", busy ? "true" : "false");
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function clearError() { errorBox.hidden = true; errorBox.textContent = ""; }

  function animateScore(target) {
    var el = $("score");
    if (reduceMotion) { el.textContent = target; return; }
    var start = performance.now(), from = parseInt(el.textContent, 10) || 0, dur = 700;
    (function frame(now) {
      var t = Math.min(1, (now - start) / dur), eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(from + (target - from) * eased);
      if (t < 1) requestAnimationFrame(frame);
    })(start);
  }

  function render(data) {
    var level = slug(data.label);
    result.dataset.level = level;
    $("label").textContent = data.label;
    $("meter").setAttribute("aria-valuenow", data.score);
    $("meter-fill").style.setProperty("--pct", data.score + "%");
    animateScore(data.score);

    var checks = $("checks");
    checks.textContent = "";
    data.checks.forEach(function (c, i) {
      var li = document.createElement("li");
      li.className = c.passed ? "ok" : "no";
      li.style.setProperty("--i", i);
      var mark = document.createElement("span");
      mark.className = "mark";
      mark.setAttribute("aria-hidden", "true");
      mark.textContent = c.passed ? "\u2713" : "\u00d7";
      var sr = document.createElement("span");
      sr.className = "sr-only";
      sr.textContent = c.passed ? "Passed: " : "Not met: ";
      li.append(mark, sr, document.createTextNode(c.label));
      checks.appendChild(li);
    });

    var tips = $("tips");
    tips.textContent = "";
    var list = data.recommendations.length
      ? data.recommendations
      : ["Excellent. No improvements needed. Use a unique password for every account."];
    list.forEach(function (text, i) {
      var li = document.createElement("li");
      li.style.setProperty("--i", i);
      if (!data.recommendations.length) li.className = "great";
      li.textContent = text;
      tips.appendChild(li);
    });

    result.hidden = false;
    result.classList.remove("is-stale");
    // restart the entrance animation
    result.classList.remove("enter");
    void result.offsetWidth;
    result.classList.add("enter");
  }

  async function check() {
    var password = input.value;
    clearError();
    if (!password) {
      showError("Please enter a password first.");
      input.focus();
      return;
    }
    var id = ++requestId;
    setBusy(true);
    try {
      var res = await fetch("/api/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: password }),
        cache: "no-store",
        credentials: "omit",
        referrerPolicy: "no-referrer"
      });
      var data = null;
      try { data = await res.json(); } catch (e) { /* non-JSON error page */ }
      if (id !== requestId) return;
      if (!res.ok || !data || !data.label) {
        showError((data && data.error) || "The server could not check this password. Please try again.");
        return;
      }
      render(data);
    } catch (e) {
      if (id === requestId) showError("Could not reach the server. Check your connection and try again.");
    } finally {
      if (id === requestId) setBusy(false);
    }
  }

  btn.addEventListener("click", check);
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); check(); } });
  input.addEventListener("input", function () {
    clearError();
    if (!result.hidden) result.classList.add("is-stale"); // results no longer match the text
  });

  toggle.addEventListener("click", function () {
    var show = input.type === "password";
    input.type = show ? "text" : "password";
    toggle.setAttribute("aria-pressed", show ? "true" : "false");
    toggle.setAttribute("aria-label", show ? "Hide password" : "Show password");
    toggle.querySelector(".eye-open").hidden = show;
    toggle.querySelector(".eye-closed").hidden = !show;
    input.focus();
  });
})();
