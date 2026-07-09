/* =============================================================
   blog-article.js — ブログ記事ページの共通処理
   ・本文の h2/h3 から目次を自動生成（＋スクロール連動ハイライト）
   ・シェアボタン（X / LINE / Facebook / リンクコピー）を配線
   ・data/blog.json を読み、前後の記事ナビを自動生成
   記事側で手書きするのは「メタ情報＋本文」だけでOK。
   ============================================================= */
(function () {
  "use strict";

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (window.__blogArticleInit) return;   // 二重実行防止
    window.__blogArticleInit = true;
    var body = document.getElementById("post-body");

    /* ---- 目次の自動生成 ---- */
    var tocWrap = document.getElementById("post-toc");
    var tocLinks = [];
    if (body && tocWrap) {
      tocWrap.innerHTML = "";
      var heads = body.querySelectorAll("h2, h3");
      if (heads.length) {
        var ul = document.createElement("ul");
        Array.prototype.forEach.call(heads, function (h, i) {
          if (!h.id) h.id = "sec-" + (i + 1);
          var li = document.createElement("li");
          if (h.tagName.toLowerCase() === "h3") li.className = "toc-sub";
          var a = document.createElement("a");
          a.href = "#" + h.id;
          a.textContent = h.textContent;
          li.appendChild(a);
          ul.appendChild(li);
          tocLinks.push({ a: a, target: h });
        });
        tocWrap.appendChild(ul);
      } else {
        var wrap = document.querySelector(".post-toc-wrap");
        if (wrap) wrap.style.display = "none";
      }
    }

    /* ---- 目次のスクロール連動ハイライト ---- */
    if (tocLinks.length && "IntersectionObserver" in window) {
      var byId = {};
      tocLinks.forEach(function (t) { byId[t.target.id] = t.a; });
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            tocLinks.forEach(function (t) { t.a.classList.remove("is-current"); });
            if (byId[e.target.id]) byId[e.target.id].classList.add("is-current");
          }
        });
      }, { rootMargin: "-110px 0px -70% 0px", threshold: 0 });
      tocLinks.forEach(function (t) { io.observe(t.target); });
    }

    /* ---- シェアボタン ---- */
    var pageUrl = location.href;
    var url = encodeURIComponent(pageUrl);
    var rawTitle = (document.title || "").split("｜")[0].trim();
    var title = encodeURIComponent(rawTitle);
    var shareMap = {
      x: "https://twitter.com/intent/tweet?text=" + title + "&url=" + url,
      line: "https://social-plugins.line.me/lineit/share?url=" + url,
      facebook: "https://www.facebook.com/sharer/sharer.php?u=" + url
    };
    Array.prototype.forEach.call(document.querySelectorAll("[data-share]"), function (el) {
      var type = el.getAttribute("data-share");
      if (type === "copy") {
        el.addEventListener("click", function (e) {
          e.preventDefault();
          var done = function () {
            el.classList.add("copied");
            setTimeout(function () { el.classList.remove("copied"); }, 1500);
          };
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(pageUrl).then(done, done);
          } else {
            var t = document.createElement("textarea");
            t.value = pageUrl; document.body.appendChild(t); t.select();
            try { document.execCommand("copy"); } catch (err) {}
            document.body.removeChild(t); done();
          }
        });
      } else if (shareMap[type]) {
        el.setAttribute("href", shareMap[type]);
        el.setAttribute("target", "_blank");
        el.setAttribute("rel", "noopener");
      }
    });

    /* ---- 前後の記事ナビ（data/blog.json から）---- */
    var nav = document.getElementById("post-nav");
    var postId = document.body.getAttribute("data-post-id");
    if (nav && postId && typeof fetch !== "undefined") {
      fetch("/data/blog.json", { cache: "no-store" })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var posts = (d && d.posts) ? d.posts : [];
          var idx = -1;
          for (var i = 0; i < posts.length; i++) {
            if (String(posts[i].id) === String(postId)) { idx = i; break; }
          }
          if (idx < 0) return;
          // posts は新しい順。idx+1 = 古い記事（前）、idx-1 = 新しい記事（次）
          var older = posts[idx + 1], newer = posts[idx - 1];
          var html = "";
          html += older
            ? '<a class="post-nav__link post-nav__prev" href="' + escapeHtml(older.url) + '"><span>前の記事</span>' + escapeHtml(older.title) + "</a>"
            : "<span></span>";
          html += newer
            ? '<a class="post-nav__link post-nav__next" href="' + escapeHtml(newer.url) + '"><span>次の記事</span>' + escapeHtml(newer.title) + "</a>"
            : "<span></span>";
          nav.innerHTML = html;
          nav.style.display = "grid";
        })
        .catch(function () { /* 取得失敗時は非表示のまま */ });
    }
  });
})();
