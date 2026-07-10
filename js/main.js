/* =============================================================
   main.js  ｜ -志遊- shiyu's station
   ・900px を境に large-screen / small-screen を body へ動的付与（debounce 200ms）
   ・ハンバーガーメニュー開閉／オーバーレイ／ドロップダウン（PC hover・タッチ click）
   ・自前スムーススクロール（500ms、ハッシュ直リンク対応）
   ・ヒーロー：クロスフェード＋ケンバーンズ（5秒間隔・インジケーター）
   ・最新動画カルーセル（.cards.reel、無限ループ・自動送り・排他制御）
   ・ページトップへ戻るボタン（300pxで表示）
   ============================================================= */
(function ($) {
  "use strict";

  var BP = 900;                 // ヘッダー切替のブレイクポイント
  var $body = $("body");

  /* ---------------------------------------------------------
     1. ブレイクポイント判定（large-screen / small-screen）
  --------------------------------------------------------- */
  function applyScreenClass() {
    if (window.innerWidth >= BP) {
      $body.addClass("large-screen").removeClass("small-screen");
    } else {
      $body.addClass("small-screen").removeClass("large-screen");
    }
  }

  function isTouch() {
    return ("ontouchstart" in window) || navigator.maxTouchPoints > 0;
  }

  /* ---------------------------------------------------------
     2. メニュー開閉
  --------------------------------------------------------- */
  function navOpen() { $body.addClass("menu-open noscroll"); $(".burger").attr("aria-expanded", "true"); }
  function navClose() { $body.removeClass("menu-open noscroll"); $(".burger").attr("aria-expanded", "false"); }

  function bindNav() {
    $(".burger").on("click", function () {
      if ($body.hasClass("menu-open")) navClose(); else navOpen();
    });
    $("#nav-scrim").on("click", navClose);

    // ドロップダウン：PC大画面は hover（CSS）、タッチ/モバイルは click
    $(".nav-menu .has-drawer > a").on("click", function (e) {
      if ($body.hasClass("small-screen") || isTouch()) {
        var $li = $(this).parent();
        // サブメニューを持つ親のリンクはトグル用途に（ページ遷移させない）
        if ($li.find(".sub").length) {
          e.preventDefault();
          $li.toggleClass("is-open").siblings(".has-drawer").removeClass("is-open");
        }
      }
    });

    // メニュー内リンク（サブメニュー親以外）をタップしたらドロワーを閉じる
    $(".nav-menu a").on("click", function () {
      var $li = $(this).parent();
      var isParentWithSub = $li.hasClass("has-drawer") && $li.children(".sub").length > 0;
      if (isParentWithSub && ($body.hasClass("small-screen") || isTouch())) return;
      navClose();
    });
  }

  /* ---------------------------------------------------------
     3. スムーススクロール（自前・500ms）
  --------------------------------------------------------- */
  var scrollType = "normal";    // 'fixed' に切替でヘッダー高さ補正が有効
  function headerOffset() {
    if (scrollType !== "fixed") return 0;
    var h = $("header").outerHeight() || 0;
    return h;
  }
  function scrollToTarget($target, dur) {
    if (!$target.length) return;
    var top = $target.offset().top - headerOffset();
    $("html,body").stop().animate({ scrollTop: top }, dur == null ? 500 : dur);
  }
  function bindSmoothScroll() {
    $(document).on("click", 'a[href^="#"]', function (e) {
      var href = $(this).attr("href");
      if (!href || href === "#") return;
      // モバイル/タッチで「サブメニューを持つ親リンク」をタップした場合は
      // スクロールせずメニュー開閉ハンドラに任せる
      var $li = $(this).parent();
      var isParentWithSub = $li.hasClass("has-drawer") && $li.children(".sub").length > 0;
      if (($body.hasClass("small-screen") || isTouch()) && isParentWithSub) return;

      var $t = $(href);
      if (!$t.length) return;
      e.preventDefault();
      if ($body.hasClass("menu-open")) navClose();
      scrollToTarget($t, 500);
      try { history.replaceState(null, "", href); } catch (err) { /* file:// 等では無視 */ }
    });

    // ハッシュ付きURLで直接開いた場合：一旦最上部→0.5秒後に該当位置へ
    if (window.location.hash && $(window.location.hash).length) {
      var hash = window.location.hash;
      window.scrollTo(0, 0);
      setTimeout(function () { scrollToTarget($(hash), 500); }, 500);
    }
  }

  /* ---------------------------------------------------------
     4. ヒーロースライドショー（クロスフェード＋ケンバーンズ）
  --------------------------------------------------------- */
  function startHero() {
    var $hero = $(".hero");
    if (!$hero.length) return;
    var $slides = $hero.find(".hero__slide");
    if ($slides.length < 2 || REDUCED) {
      $slides.eq(0).addClass("is-active");
      if (!REDUCED) $slides.eq(0).addClass("is-zoom");
      return;
    }

    var INTERVAL = 5000;
    var cur = 0, timer = null;

    // フェード時間を CSS から動的取得（同期のため）
    function fadeDurMs() {
      var v = getComputedStyle($slides[0]).transitionDuration || "1s";
      v = v.split(",")[0].trim();
      return v.indexOf("ms") > -1 ? parseFloat(v) : parseFloat(v) * 1000;
    }

    // インジケーター生成
    var $dots = $('<div class="hero__dots" role="tablist" aria-label="スライド切替"></div>');
    $slides.each(function (i) {
      $('<button type="button" aria-label="' + (i + 1) + '枚目へ"></button>')
        .toggleClass("is-active", i === 0)
        .on("click", function () { go(i); resetTimer(); })
        .appendTo($dots);
    });
    $hero.find(".hero__slides").append($dots);

    $slides.eq(0).addClass("is-active is-zoom");

    function go(next) {
      if (next === cur) return;
      var prev = cur;
      cur = next;
      var $next = $slides.eq(cur), $prev = $slides.eq(prev);

      $next.addClass("is-active is-zoom");                 // フェードイン＋ズーム開始
      $dots.children().removeClass("is-active").eq(cur).addClass("is-active");

      setTimeout(function () {
        $prev.removeClass("is-active");                    // フェード完了後に前面を消す
        // 前スライドのズームを瞬時にリセット（transition を一時停止）
        var img = $prev.find("img")[0];
        if (img) {
          img.style.transition = "none";
          $prev.removeClass("is-zoom");
          void img.offsetWidth;                            // 強制リフロー
          img.style.transition = "";
        }
      }, fadeDurMs());
    }

    function tick() { go((cur + 1) % $slides.length); }
    function startTimer() { timer = setInterval(tick, INTERVAL); }
    function resetTimer() { clearInterval(timer); startTimer(); }

    startTimer();
    // タブ非表示中は停止（無駄な描画抑制）
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) clearInterval(timer); else resetTimer();
    });
  }

  /* ---------------------------------------------------------
     5. 最新動画カルーセル（.cards.reel）
        自動送り＋左右矢印＋スワイプ＋ドット。reduced-motion時は自動送り停止。
  --------------------------------------------------------- */
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function initReels() {
    $(".cards.reel").each(function () {
      new Reel($(this));
    });
  }

  function Reel($root) {
    this.$root = $root;

    // スクロールイン演出とは相性が悪いため reveal 系のクラス・属性を除去
    $root.removeClass("reveal").removeAttr("data-reveal");
    $root.find(".reveal").removeClass("reveal is-revealed").removeAttr("data-reveal");

    // 元のカードを退避し .track に詰め直す
    var $originals = $root.children().not(".dots");
    this.count = $originals.length;
    if (this.count === 0) return;

    this.$track = $('<div class="track"></div>');
    $originals.appendTo(this.$track);
    $root.empty().append(this.$track);
    this.$dots = $('<div class="dots" role="tablist" aria-label="スライド位置"></div>').appendTo($root);

    // 左右矢印
    this.$prev = $('<button type="button" class="car-nav car-nav--prev" aria-label="前へ"><i class="fa-solid fa-chevron-left"></i></button>').appendTo($root);
    this.$next = $('<button type="button" class="car-nav car-nav--next" aria-label="次へ"><i class="fa-solid fa-chevron-right"></i></button>').appendTo($root);

    this.index = 0;
    this.animating = false;
    this.pending = null;
    this.timer = null;
    this.AUTO = 4000;
    this.DUR = 1000;

    this.layout();
    this.buildDots();
    this.bind();
    if (!REDUCED) this.start();
  }

  Reel.prototype.metrics = function () {
    var w = window.innerWidth;
    this.perView = w > 800 ? 4 : 2;   // PCは4枚・モバイルは2枚
    this.step = w > 800 ? 2 : 1;      // 2枚送り / 1枚送り
    this.perView = Math.min(this.perView, this.count);
  };

  Reel.prototype.layout = function () {
    this.metrics();
    var gap = parseFloat(getComputedStyle(this.$track[0]).columnGap || getComputedStyle(this.$track[0]).gap || "16") || 16;
    this.gap = gap;
    var containerW = this.$root.width();
    this.itemW = (containerW - gap * (this.perView - 1)) / this.perView;

    // クローンを作り直し（無限ループ用に先頭 perView 枚を末尾へ）
    this.$track.find(".is-clone").remove();
    var $items = this.$track.children();
    for (var i = 0; i < this.perView; i++) {
      $items.eq(i).clone(true).addClass("is-clone").appendTo(this.$track);
    }
    this.$all = this.$track.children();
    this.$all.css("width", this.itemW + "px");

    this.index = 0;
    this.place(false);
  };

  Reel.prototype.place = function (animate) {
    var x = -(this.index * (this.itemW + this.gap));
    this.$track.css("transition", animate ? ("transform " + this.DUR + "ms cubic-bezier(.22,.61,.36,1)") : "none");
    this.$track.css("transform", "translateX(" + x + "px)");
    if (!animate) { void this.$track[0].offsetWidth; }
  };

  Reel.prototype.buildDots = function () {
    var self = this;
    this.pages = Math.max(1, Math.ceil(this.count / this.step));
    this.$dots.empty();
    for (var p = 0; p < this.pages; p++) {
      (function (p) {
        $('<button type="button" aria-label="' + (p + 1) + '番目の位置へ"></button>')
          .toggleClass("is-active", p === 0)
          .on("click", function () { self.jumpToPage(p); self.restart(); })
          .appendTo(self.$dots);
      })(p);
    }
  };

  Reel.prototype.updateDots = function () {
    var page = Math.round(this.index / this.step) % this.pages;
    if (page < 0) page += this.pages;
    this.$dots.children().removeClass("is-active").eq(page).addClass("is-active");
  };

  Reel.prototype.next = function () {
    if (this.animating) { this.pending = { type: "next" }; return; }
    this.animating = true;
    this.index += this.step;
    this.place(true);
  };

  Reel.prototype.prev = function () {
    if (this.animating) { this.pending = { type: "prev" }; return; }
    this.animating = true;
    if (this.index - this.step < 0) {
      // クローン域を使って瞬時に一巡先へ寄せてから戻す（切れ目なし）
      this.index += this.count;
      this.place(false);
    }
    this.index -= this.step;
    this.place(true);
  };

  Reel.prototype.jumpToPage = function (p) {
    var target = p * this.step;
    if (this.animating) { this.pending = { type: "page", page: p }; return; }
    if (target === this.index % this.count) return;
    this.animating = true;
    this.index = target;
    this.place(true);
  };

  Reel.prototype.onEnd = function () {
    this.animating = false;
    // 末尾（クローン域）に達したら瞬時に先頭へ戻す
    if (this.index >= this.count) {
      this.index = this.index - this.count;
      this.place(false);
    }
    this.updateDots();
    // 予約されていた操作を実行
    if (this.pending) {
      var p = this.pending; this.pending = null;
      if (p.type === "next") this.next();
      else if (p.type === "prev") this.prev();
      else if (p.type === "page") this.jumpToPage(p.page);
    }
  };

  Reel.prototype.start = function () {
    if (REDUCED) return;
    var self = this;
    clearInterval(this.timer);
    this.timer = setInterval(function () { self.next(); }, this.AUTO);
  };
  Reel.prototype.stop = function () { clearInterval(this.timer); };
  Reel.prototype.restart = function () { this.stop(); this.start(); };

  Reel.prototype.bind = function () {
    var self = this;
    this.$track.on("transitionend", function (e) {
      if (e.target === self.$track[0] && e.originalEvent.propertyName === "transform") self.onEnd();
    });
    this.$root.on("mouseenter", function () { self.stop(); })
              .on("mouseleave", function () { self.start(); });

    // 矢印
    this.$prev.on("click", function () { self.prev(); self.restart(); });
    this.$next.on("click", function () { self.next(); self.restart(); });

    // スワイプ（横40px以上で送り。縦スクロールは妨げない）
    var sx = 0, sy = 0, swiping = false;
    this.$root.on("touchstart", function (e) {
      var t = e.originalEvent.touches[0];
      sx = t.clientX; sy = t.clientY; swiping = true;
      self.stop();
    });
    this.$root.on("touchend", function (e) {
      if (!swiping) return;
      swiping = false;
      var t = e.originalEvent.changedTouches[0];
      var dx = t.clientX - sx, dy = t.clientY - sy;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
        if (dx < 0) self.next(); else self.prev();
      }
      self.start();
    });

    // リサイズは 250ms デバウンスで再初期化
    var rt;
    $(window).on("resize.carousel", function () {
      clearTimeout(rt);
      rt = setTimeout(function () {
        self.stop();
        self.layout();
        self.buildDots();
        self.start();
      }, 250);
    });
  };

  /* ---------------------------------------------------------
     6. ページトップへ戻る
  --------------------------------------------------------- */
  function bindPagetop() {
    var $btn = $(".to-top");
    var $header = $("header");
    $(window).on("scroll", function () {
      var y = window.pageYOffset;
      if ($btn.length) { if (y > 300) $btn.addClass("is-show"); else $btn.removeClass("is-show"); }
      if ($header.length) { if (y > 10) $header.addClass("is-scrolled"); else $header.removeClass("is-scrolled"); }
    });
    if ($btn.length) $btn.on("click", function () { $("html,body").stop().animate({ scrollTop: 0 }, 500); });
  }

  /* ---------------------------------------------------------
     7. 路線図スクロールインジケーター（現在地の点灯のみ。
        クリック移動は既存の bindSmoothScroll に委譲）
  --------------------------------------------------------- */
  function initRouteMap() {
    var stops = Array.prototype.slice.call(document.querySelectorAll(".routemap__stop"));
    if (!stops.length || !("IntersectionObserver" in window)) return;
    var secs = stops.map(function (a) {
      return document.getElementById((a.getAttribute("href") || "").slice(1));
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var i = secs.indexOf(en.target);
        if (i < 0) return;
        stops.forEach(function (st, j) {
          st.classList.toggle("is-active", j === i);
          st.classList.toggle("is-passed", j < i);
        });
      });
    }, { rootMargin: "-45% 0px -45% 0px" });
    secs.forEach(function (s) { if (s) io.observe(s); });
  }

  /* ---------------------------------------------------------
     9. 方向幕（split-flap）行先表示：SHIYU / TRAVEL / RAILWAY / TAIKO
  --------------------------------------------------------- */
  function initFlap() {
    var board = document.getElementById("flap-board");
    if (!board) return;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion:reduce)").matches;
    var CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ ";
    var WORDS = ["SHIYU", "TRAVEL", "RAILWAY", "TAIKO"];
    var CELLS = 7, cells = [], i;
    for (i = 0; i < CELLS; i++) {
      var c = document.createElement("span");
      c.className = "flap-cell";
      c.textContent = " ";
      board.appendChild(c);
      cells.push(c);
    }
    function setBoard(word) {
      word = (word + "       ").slice(0, CELLS);
      cells.forEach(function (cell, idx) {
        var target = word.charAt(idx);
        if (reduce) { cell.textContent = target; return; }
        var steps = 6 + idx * 2, n = 0;
        var iv = setInterval(function () {
          cell.textContent = CHARS.charAt(Math.floor(Math.random() * CHARS.length));
          cell.classList.add("is-flip");
          setTimeout(function () { cell.classList.remove("is-flip"); }, 90);
          if (++n >= steps) { clearInterval(iv); cell.textContent = target; }
        }, 55);
      });
    }
    var di = 0;
    setBoard(WORDS[0]);
    if (!reduce) setInterval(function () { di = (di + 1) % WORDS.length; setBoard(WORDS[di]); }, 3200);
  }

  /* ---------------------------------------------------------
     10. 改札ゲート遷移（内部ページへの遷移を一瞬の暗転で演出）
  --------------------------------------------------------- */
  function initGate() {
    var gate = document.getElementById("gate");
    if (!gate) return;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion:reduce)").matches;
    if (reduce) return;
    var toEl = document.getElementById("gate-to");
    var THIS = (location.pathname.split("/").pop() || "index.html");
    // ページ種別 → ラベル
    var PAGE = { "index.html": "HOME", "": "HOME", "kiroku.html": "KIROKU", "blog.html": "BLOG", "contact.html": "CONTACT", "privacy.html": "PRIVACY" };
    // ページ内セクション（＝クリックした項目）→ ラベル。ハッシュがあれば優先
    var SECTION = { "top": "HOME", "about": "ABOUT", "latest": "LATEST", "category": "CATEGORY", "rail": "RAIL", "taiko": "TAIKO", "links": "CHANNELS", "news": "NEWS", "contact": "CONTACT" };

    // 行先ラベル：クリック先にハッシュ（具体的な項目）があればそれを、
    // 無ければ遷移先ページ種別を表示する。
    function labelFor(hash, file) {
      var id = (hash || "").replace(/^#/, "");
      if (id && SECTION[id]) return SECTION[id];
      return PAGE[file] || "STATION";
    }

    function reset() { gate.classList.remove("is-visible", "is-closing", "is-opening"); }

    // 到着時：改札が開く演出（URL にハッシュがあればその項目名を表示）
    function playOpen() {
      if (toEl) toEl.textContent = labelFor(location.hash, THIS);
      reset();
      gate.classList.add("is-visible", "is-opening");
      window.setTimeout(reset, 1250);  // 開き終わったら隠す（アニメ 1.15s + 余白）
    }

    // 出発時：改札が閉じてから移動（クリックした項目名を表示）
    function playCloseThen(href) {
      var hash = href.indexOf("#") >= 0 ? href.slice(href.indexOf("#")) : "";
      var file = href.split("#")[0].split("/").pop();
      if (toEl) toEl.textContent = labelFor(hash, file);
      reset();
      gate.classList.add("is-visible", "is-closing");
      window.setTimeout(function () { window.location.href = href; }, 360);
    }

    document.addEventListener("click", function (e) {
      var a = e.target.closest ? e.target.closest("a") : null;
      if (!a) return;
      if (a.target === "_blank" || a.hasAttribute("download")) return;
      if (a.origin && a.origin !== location.origin) return;   // 外部リンク
      if (a.pathname === location.pathname) return;            // 同一ページ内リンク
      var href = a.getAttribute("href") || "";
      var file = href.split("#")[0].split("/").pop();
      if (!/\.html$/.test(file)) return;                       // .html 遷移のみ対象
      e.preventDefault();
      playCloseThen(href);
    });

    // 初回表示で開く演出。ブラウザバック（bfcache 復帰）時は閉じたまま
    // 固まらないよう、必ずリセットしてから開き直す。
    window.addEventListener("pageshow", function (e) { if (e.persisted) playOpen(); });
    playOpen();
  }

  /* ---------------------------------------------------------
     初期化
  --------------------------------------------------------- */
  $(function () {
    applyScreenClass();
    bindNav();
    bindSmoothScroll();
    bindPagetop();
    startHero();
    initReels();
    initRouteMap();
    initFlap();
    initGate();

    // リサイズで screen クラス再判定（debounce 200ms）
    var t;
    $(window).on("resize", function () {
      clearTimeout(t);
      t = setTimeout(applyScreenClass, 200);
    });
  });
})(jQuery);
