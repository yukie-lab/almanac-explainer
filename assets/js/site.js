// Language switch (English / Japanese), subtitle track choice, and transcript seeking.
(function () {
  "use strict";
  var KEY = "almanac-explainer-lang";
  var root = document.documentElement;
  var video = document.getElementById("video");
  var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-set-lang]"));
  var titles = {
    en: "Where will Proxima b be when a probe arrives? · A plain-language guide",
    ja: "探査機が着くとき、プロキシマ b はどこにいるか · やさしい解説"
  };

  function initial() {
    var q = null;
    try { q = new URLSearchParams(window.location.search).get("lang"); } catch (e) { q = null; }
    if (q === "en" || q === "ja") return q;
    try {
      var saved = window.localStorage.getItem(KEY);
      if (saved === "en" || saved === "ja") return saved;
    } catch (e) { /* storage may be blocked */ }
    return "en";
  }

  function setTracks(lang) {
    if (!video || !video.textTracks) return;
    for (var i = 0; i < video.textTracks.length; i++) {
      var t = video.textTracks[i];
      if (t.kind !== "subtitles") continue;
      t.mode = t.language === lang ? "showing" : "disabled";
    }
  }

  function apply(lang, remember) {
    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", lang);
    document.title = titles[lang];
    buttons.forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-set-lang") === lang ? "true" : "false");
    });
    setTracks(lang);
    // Accessible names and hover texts that live in attributes follow the language too.
    Array.prototype.forEach.call(document.querySelectorAll("[data-aria-" + lang + "]"), function (el) {
      el.setAttribute("aria-label", el.getAttribute("data-aria-" + lang));
    });
    Array.prototype.forEach.call(document.querySelectorAll("title[data-" + lang + "]"), function (el) {
      el.textContent = el.getAttribute("data-" + lang);
    });
    if (!remember) return;
    try { window.localStorage.setItem(KEY, lang); } catch (e) { /* ignore */ }
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("lang", lang);
      window.history.replaceState(null, "", url.toString());
    } catch (e) { /* ignore */ }
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () { apply(b.getAttribute("data-set-lang"), true); });
  });

  var lang = initial();
  apply(lang, false);
  if (video && video.textTracks && video.textTracks.addEventListener) {
    // Tracks can register after this script runs; set them again when they do.
    video.textTracks.addEventListener("addtrack", function () { setTracks(root.getAttribute("data-lang") || "en"); });
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-seek]"), function (b) {
    b.addEventListener("click", function () {
      if (!video) return;
      video.currentTime = parseFloat(b.getAttribute("data-seek")) || 0;
      video.scrollIntoView({ behavior: "smooth", block: "center" });
      var p = video.play();
      if (p && p.catch) p.catch(function () { /* autoplay may be refused */ });
    });
  });
})();
