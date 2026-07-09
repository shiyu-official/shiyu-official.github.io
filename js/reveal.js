/* =============================================================
   reveal.js — スクロール登場モーションの制御（依存ライブラリなし）
   .reveal 要素を IntersectionObserver で監視し、ビューポートに入った
   ものから .is-revealed を付けて reveal.css のモーションを発火させる。
   種類は要素の data-reveal →無ければ最寄り祖先の data-reveal →既定 "rise"。
   一度表示した要素は監視を外す（再生は入場時の一回だけ）。
   ============================================================= */
(function () {
  "use strict";

  var SELECTOR = ".reveal";
  var SHOWN = "is-revealed";
  var ATTR = "data-reveal";
  var DEFAULT = "rise";

  function kindOf(el) {
    if (el.getAttribute(ATTR)) return el.getAttribute(ATTR);
    var host = el.closest("[" + ATTR + "]");
    if (host && host !== el) return host.getAttribute(ATTR);
    return DEFAULT;
  }

  function show(el) { el.classList.add(SHOWN); }

  function start() {
    var items = Array.prototype.slice.call(document.querySelectorAll(SELECTOR));
    if (!items.length) return;

    // 種類を各要素に確定させておく（CSSの開始状態を安定させる）
    items.forEach(function (el) { el.setAttribute(ATTR, kindOf(el)); });

    // 非対応ブラウザでは即表示（真っ白を防ぐ）
    if (!("IntersectionObserver" in window)) {
      items.forEach(show);
      return;
    }

    var watcher = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          show(e.target);
          obs.unobserve(e.target);
        }
      });
    }, { root: null, rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

    items.forEach(function (el) { watcher.observe(el); });

    // 保険：発火漏れに備え、一定時間後に画面内の要素を表示
    window.setTimeout(function () {
      var vh = window.innerHeight || document.documentElement.clientHeight;
      items.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < vh && r.bottom > 0) show(el);
      });
    }, 1200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
