/* YZH的Blog — 终端交互：打字机与唯一光标、码字点击粒子、滚动进度条、回到顶部 */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- 滚动进度条 ---------- */
  var progress = document.getElementById("scroll-progress");
  if (progress) {
    var update = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      progress.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    };
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  /* ---------- 回到顶部 ---------- */
  var backTop = document.getElementById("back-top");
  if (backTop) {
    var onScroll = function () {
      backTop.classList.toggle("visible", (window.scrollY || document.documentElement.scrollTop) > 480);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    backTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
  }

  /* ---------- Hero 打字机 + 唯一光标 ----------
     规则：同一时刻只有一个光标闪烁。
     打字中光标在输出行；打字完成后光标移动到最后一行的输入位置。 */
  var typeTarget = document.getElementById("typewriter");
  var twCursor = document.getElementById("tw-cursor");
  var tailCursor = document.getElementById("tail-cursor");

  function moveCursorToTail() {
    if (twCursor) twCursor.hidden = true;
    if (tailCursor) tailCursor.hidden = false;
  }

  if (typeTarget && twCursor && tailCursor) {
    var fullText = typeTarget.getAttribute("data-text") || "";
    if (reduceMotion || !fullText) {
      typeTarget.textContent = fullText;
      moveCursorToTail();
    } else {
      var i = 0;
      var timer = setInterval(function () {
        i += 1;
        typeTarget.textContent = fullText.slice(0, i);
        if (i >= fullText.length) {
          clearInterval(timer);
          moveCursorToTail();
        }
      }, 26);
    }
  }

  /* ---------- 代码块复制按钮 ---------- */
  var copyLabel = "copy";
  var doneLabel = "✓ copied";
  document.querySelectorAll(".codeblock-bar").forEach(function (bar) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.textContent = copyLabel;
    btn.setAttribute("aria-label", "复制代码");
    btn.addEventListener("click", function () {
      var pre = bar.parentElement.querySelector(".highlight pre");
      if (!pre) return;
      var text = pre.textContent;
      var ok = function () {
        btn.textContent = doneLabel;
        btn.classList.add("done");
        setTimeout(function () {
          btn.textContent = copyLabel;
          btn.classList.remove("done");
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(ok, function () { fallbackCopy(text, ok); });
      } else {
        fallbackCopy(text, ok);
      }
    });
    bar.appendChild(btn);
  });

  function fallbackCopy(text, done) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); done(); } catch (e) { /* noop */ }
    document.body.removeChild(ta);
  }

  /* ---------- 点击粒子特效（码字爆散） ---------- */
  var PARTICLE_CHARS = ["$", "#", "&", "<", ">", "{", "}", "/", "\\", "(", ")", "_", "+", "=", "*", "~"];
  var PARTICLE_COLORS = ["#7dcfff", "#9ece6a", "#bb9af7", "#e0af68", "#7aa2f7"];

  function spawnParticles(x, y) {
    var n = 10;
    for (var i = 0; i < n; i++) {
      var s = document.createElement("span");
      s.className = "click-particle";
      s.textContent = PARTICLE_CHARS[Math.floor(Math.random() * PARTICLE_CHARS.length)];
      s.style.color = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
      s.style.left = x + "px";
      s.style.top = y + "px";
      var angle = Math.random() * Math.PI * 2;
      var dist = 28 + Math.random() * 44;
      s.style.setProperty("--dx", (Math.cos(angle) * dist).toFixed(1) + "px");
      s.style.setProperty("--dy", (Math.sin(angle) * dist - 18).toFixed(1) + "px");
      s.style.setProperty("--rot", (Math.random() * 200 - 100).toFixed(0) + "deg");
      s.style.textShadow = "0 0 8px " + s.style.color;
      document.body.appendChild(s);
      (function (el) { setTimeout(function () { el.remove(); }, 650); })(s);
    }
  }

  document.addEventListener("pointerdown", function (e) {
    if (reduceMotion) return;
    if (e.button !== 0 && e.pointerType !== "touch") return;
    // 文本选择时不出粒子，避免干扰
    var sel = window.getSelection();
    if (sel && sel.toString()) return;
    spawnParticles(e.clientX, e.clientY);
  });
})();
