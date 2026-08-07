/* YZH的Blog — 站内全文搜索（本地索引，无后端） */
(function () {
  "use strict";

  const input = document.getElementById("search-input");
  const results = document.getElementById("search-results");
  if (!input || !results || typeof INDEX_URL === "undefined") return;

  let index = null;
  let initialQ = null;
  try { initialQ = new URLSearchParams(window.location.search).get("q"); } catch (e) { /* noop */ }
  if (initialQ) input.value = initialQ;

  function runSearch() {
    if (!index) return;
    var qs = norm(input.value).split(/\s+/).filter(Boolean);
    if (!qs.length) {
      results.innerHTML = '<p class="search-hint">输入关键词，即时搜索标题、摘要与正文。</p>';
      return;
    }
    render(index.filter(function (p) { return matches(p, qs); }), qs);
  }

  fetch(INDEX_URL, { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (data) {
      index = data.posts || [];
      if (initialQ) {
        runSearch();
      } else {
        results.innerHTML = '<p class="search-hint">索引已加载（' + index.length + ' 篇文章），输入关键词开始搜索。</p>';
      }
    })
    .catch(function () {
      results.innerHTML = '<p class="search-hint">索引加载失败：' + INDEX_URL + ' 不存在，请先运行 uv run build.py。</p>';
    });

  function norm(s) { return String(s || "").toLowerCase(); }

  function matches(post, qs) {
    var tagText = (post.tags || []).map(function (t) { return t.name; }).join(" ");
    var hay = norm(post.title + " " + post.summary + " " + post.text + " " + post.category + " " + tagText + " " + post.date);
    return qs.every(function (q) { return hay.indexOf(q) !== -1; });
  }

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function highlight(text, qs) {
    var out = escapeHtml(text);
    qs.forEach(function (q) {
      if (q.length < 1) return;
      var re = new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  function render(list, qs) {
    if (!list.length) {
      results.innerHTML = '<p class="search-empty">无匹配结果。</p>';
      return;
    }
    var html = list.slice(0, 30).map(function (p) {
      var tags = (p.tags || []).map(function (t) { return "#" + t.name; }).join(" ");
      var meta = [p.date, p.category, tags].filter(Boolean).join(" · ");
      return (
        '<div class="search-result">' +
        '<h3 class="search-result-title"><a href="' + p.url + '">' + highlight(p.title, qs) + "</a></h3>" +
        '<div class="search-result-meta">' + highlight(meta, qs) + "</div>" +
        '<p class="search-result-summary">' + highlight(p.summary, qs) + "</p>" +
        "</div>"
      );
    }).join("");
    html += list.length > 30 ? '<p class="search-empty">… 还有 ' + (list.length - 30) + " 条结果（仅显示前 30 条）</p>" : "";
    results.innerHTML = html;
  }

  var timer = null;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(runSearch, 120);
  });
})();
