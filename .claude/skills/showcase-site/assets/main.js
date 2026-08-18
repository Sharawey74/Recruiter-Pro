/*
 * Two small behaviours. No framework, no build step — the page is static and
 * works with this file blocked.
 */
(function () {
  "use strict";

  /**
   * Mark the current page in the nav.
   *
   * Done here rather than by hand in three files so a renamed page cannot end
   * up highlighted on the wrong one. Falls back to index.html for a bare
   * directory URL, which is what GitHub Pages serves at the site root.
   */
  function markCurrentPage() {
    var here = location.pathname.split("/").pop() || "index.html";
    var links = document.querySelectorAll(".nav a");

    for (var i = 0; i < links.length; i++) {
      var target = links[i].getAttribute("href");
      if (target === here) {
        links[i].setAttribute("aria-current", "page");
      } else {
        links[i].removeAttribute("aria-current");
      }
    }
  }

  /**
   * Fade sections in as they arrive.
   *
   * Guarded twice. Without IntersectionObserver, or under
   * prefers-reduced-motion, every element is revealed immediately instead of
   * being left invisible — content must never depend on an animation having
   * run to become readable.
   */
  function revealOnScroll() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    var still =
      !("IntersectionObserver" in window) ||
      (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

    if (still) {
      for (var i = 0; i < items.length; i++) items[i].classList.add("is-in");
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.06 }
    );

    for (var j = 0; j < items.length; j++) observer.observe(items[j]);
  }

  function init() {
    markCurrentPage();
    revealOnScroll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
