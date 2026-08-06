/* YZH的Blog — 终端交互：打字机、代码复制、滚动进度条 */
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

  /* ---------- Hero 打字机 ---------- */
  var typeTarget = document.getElementById("typewriter");
  if (typeTarget) {
    var fullText = typeTarget.getAttribute("data-text") || "";
    if (reduceMotion) {
      typeTarget.textContent = fullText;
    } else {
      var i = 0;
      var timer = setInterval(function () {
        i += 1;
        typeTarget.textContent = fullText.slice(0, i);
        if (i >= fullText.length) clearInterval(timer);
      }, 28);
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
})();
