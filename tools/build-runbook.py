#!/usr/bin/env python3
"""서버 구축 런북(.ini/.txt) → 자체 완결형 HTML 한 파일로 빌드.

CSS·JS·데이터·아이콘을 모두 인라인하므로 인터넷 없이 더블클릭으로 열린다.
사내 자료는 이 저장소에 두지 않고, 빌드할 때만 외부 경로로 넘긴다.

사용법:
    python3 tools/build-runbook.py <런북.ini> [출력.html] [--title "제목"]

입력 형식(원본 문서 구조를 그대로 따른다):
    ===...===        구분선 — 이 다음 줄이 대제목
    N. / N-M. 제목   대제목
    # 제목           대제목(후반부 샘플 블록)
       - 중제목
         ; 소제목
         # 명령어
           > 값
         ★ 주의

자격증명으로 보이는 값은 화면에서 기본으로 흐리게 처리된다(어깨너머 방지용
편의 기능이며 암호화가 아니다). 상단 토글로 표시/숨김을 바꾼다.
"""
import html
import os
import re
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "assets", "css", "site.scss")

SEP = re.compile(r"^={40,}\s*$")
H_NUM = re.compile(r"^(\d+(?:-\d+)?)\.\s+(.*)$")
H_HASH = re.compile(r"^#\s*(.+?)\s*$")

# 자격증명이 나타나는 문맥. 각 패턴의 'v' 그룹만 가린다.
SECRET_PATTERNS = [
    re.compile(r"(?P<a>_PW\s*=\s*)(?P<v>\S+)"),
    re.compile(r"(?P<a>identified\s+by\s+')(?P<v>[^']+)(?P<b>')", re.I),
    re.compile(r"(?P<a>password\s+')(?P<v>[^']+)(?P<b>')", re.I),
    re.compile(r"(?P<a>echo\s+')(?P<v>[^']+)(?P<b>'\s*\|\s*passwd)"),
    re.compile(r"(?P<a>(?:New password|Re-enter new password|Enter current password[^:]*)\s*:\s*)(?P<v>\S+)"),
    re.compile(r"(?P<a>\s-p)(?P<v>[^\s'\"]{3,})"),
    re.compile(r"(?P<a>;\s*(?:OS|Mariadb)\s*:\s*[\w.-]+\s*/\s*)(?P<v>\S+)"),
    re.compile(r"(?P<a>>\s*[\w.-]+\s*/\s*)(?P<v>\S+)"),
]

SENT_O, SENT_C = "\x00", "\x01"


def collect_and_mark(line, vault):
    """자격증명 자리를 sentinel 로 감싸고, 그 값을 vault 에 모은다(출력하지 않음)."""
    out = line
    for pat in SECRET_PATTERNS:
        def repl(m):
            v = m.group("v")
            if v.lower() in ("none", "null", "yes", "no", "root") or len(v) < 3:
                return m.group(0)
            vault.add(v)
            rest = m.group("b") if "b" in m.groupdict() and m.group("b") else ""
            return m.group("a") + SENT_O + v + SENT_C + rest
        out = pat.sub(repl, out)
    return out


def mark_known(line, vault):
    """앞서 수집된 값이 다른 자리에 또 나오면 같이 가린다."""
    for v in sorted(vault, key=len, reverse=True):
        if v in line and SENT_O + v + SENT_C not in line:
            line = line.replace(v, SENT_O + v + SENT_C)
    return line


def render_line(raw, vault):
    marked = mark_known(collect_and_mark(raw, vault), vault)
    esc = html.escape(marked)
    esc = esc.replace(html.escape(SENT_O), '<span class="secret">').replace(
        html.escape(SENT_C), "</span>"
    )
    esc = esc.replace(SENT_O, '<span class="secret">').replace(SENT_C, "</span>")

    body = raw.lstrip()
    if body.startswith("- "):
        cls = "l-sub"
    elif body.startswith("; "):
        cls = "l-lbl"
    elif body.startswith("# "):
        cls = "l-cmd"
    elif body.startswith("> "):
        cls = "l-val"
    elif body.startswith("★"):
        cls = "l-warn"
    elif body.startswith("MariaDB ") or body.startswith("mysql>"):
        cls = "l-sql"
    elif not body:
        cls = "l-blank"
    else:
        cls = "l-txt"
    return f'<span class="ln {cls}">{esc}</span>'


def parse(path):
    lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
    sections, cur = [], None
    expect_title = True
    for raw in lines:
        if SEP.match(raw):
            expect_title = True
            continue
        if expect_title:
            if not raw.strip():
                continue
            m = H_NUM.match(raw.strip())
            if m:
                num, title = m.group(1), m.group(2)
            else:
                m2 = H_HASH.match(raw.strip())
                if m2:
                    num, title = "", m2.group(1)
                else:
                    # 제목 형태가 아니면 이전 섹션의 본문으로 취급
                    if cur:
                        cur["lines"].append(raw)
                    continue
            cur = {"num": num, "title": title, "lines": []}
            sections.append(cur)
            expect_title = False
            continue
        if cur is not None:
            cur["lines"].append(raw)
    # 뒤쪽 빈 줄 정리
    for s in sections:
        while s["lines"] and not s["lines"][-1].strip():
            s["lines"].pop()
    return [s for s in sections if s["lines"]]


def group_of(sec):
    n = sec["num"]
    if n.startswith(("1", "2")) and "." not in n[:1] + "x":
        pass
    head = n.split("-")[0] if n else ""
    return {
        "1": "서버 정보",
        "2": "서버 정보",
        "3": "서버 구성",
        "4": "MariaDB",
        "5": "패키지",
        "6": "패키지",
        "7": "패키지",
        "8": "패키지",
        "9": "패키지",
        "10": "패키지",
    }.get(head, "샘플·참고")


def build(src, out_path=None, title=None):
    sections = parse(src)
    base = os.path.basename(src)
    title = title or "녹취 패키지 구축 런북"
    out_path = out_path or "runbook.html"

    css = open(CSS, encoding="utf-8").read()
    if css.lstrip().startswith("---"):
        parts = css.split("---", 2)
        css = parts[2] if len(parts) > 2 else css

    # 1패스: 문서 전체를 훑어 자격증명을 모은다.
    # (한 번만 훑으면 값이 처음 발견된 줄보다 앞에 나온 같은 값을 놓친다)
    vault = set()
    for sec in sections:
        for l in sec["lines"]:
            collect_and_mark(l, vault)

    cards, chips = [], []
    groups = []
    for i, sec in enumerate(sections):
        g = group_of(sec)
        if g not in groups:
            groups.append(g)
        num = f"{sec['num']}. " if sec["num"] else ""
        # 각 줄 span 이 display:block 이므로 사이에 개행을 넣으면 간격이 두 배가 된다.
        body = "".join(render_line(l, vault) for l in sec["lines"])
        sid = f"sec-{i}"
        cards.append(
            f'<div class="card sec" id="{sid}" data-group="{html.escape(g)}">'
            f'<div class="card-head">'
            f'<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'
            f'<div class="card-head-main"><div class="card-name-row">'
            f'<span class="card-name">{html.escape(num + sec["title"])}</span>'
            f'<span class="card-cat">{html.escape(g)}</span>'
            f"</div></div>"
            f'<div class="card-meta"><span class="meta-pill">{len(sec["lines"])}줄</span></div>'
            f"</div>"
            f'<div class="card-body"><pre class="run">{body}</pre></div>'
            f"</div>"
        )

    for g in groups:
        n = sum(1 for s in sections if group_of(s) == g)
        chips.append(f'<div class="chip" data-group="{html.escape(g)}">{html.escape(g)}<span class="n">{n}</span></div>')

    icon = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#0E1513"/>'
        '<path d="M14 18h36M14 30h26M14 42h32" stroke="#59B7A4" stroke-width="4.5" stroke-linecap="round"/>'
        '<circle cx="47" cy="42" r="6" fill="none" stroke="#E0B15C" stroke-width="4"/>'
        "</svg>"
    )
    favicon = "data:image/svg+xml," + quote(icon)

    doc = f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0E1513">
<meta name="application-name" content="{html.escape(title)}">
<title>{html.escape(title)}</title>
<link rel="icon" href="{favicon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
{css}
header.top {{ padding: 18px 0 14px; }}
.notice {{
  margin: 18px 0 0; padding: 11px 14px; border-radius: var(--radius);
  background: var(--required-soft); border: 1px solid rgba(226,142,130,.35);
  color: var(--required); font-size: 13px; line-height: 1.5;
}}
.card.sec .card-body {{ padding: 0; }}
pre.run {{
  margin: 0; padding: 14px 16px; overflow-x: auto;
  font-family: var(--mono); font-size: 12.5px; line-height: 1.62;
  background: #0B1211; color: #C6D3CF; tab-size: 4;
}}
.ln {{ display: block; white-space: pre; border-radius: 3px; min-height: 1.62em; }}
.ln.l-sub  {{ color: #7ECAB9; font-weight: 600; margin-top: 6px; }}
.ln.l-lbl  {{ color: #9AACA5; }}
.ln.l-cmd  {{ color: #E7EFED; cursor: pointer; }}
.ln.l-cmd:hover {{ background: rgba(89,183,164,.10); }}
.ln.l-cmd.copied {{ background: rgba(89,183,164,.22); }}
.ln.l-val  {{ color: #9FD3F0; }}
.ln.l-sql  {{ color: #C3D98E; }}
.ln.l-warn {{ color: #E0B15C; }}
.ln.l-txt  {{ color: #93A29D; }}
.ln mark {{ background: var(--key-soft); color: var(--text); border-radius: 3px; padding: 0 1px; }}
.secret {{ filter: blur(4.5px); transition: filter .12s; border-radius: 3px; }}
body.reveal .secret {{ filter: none; background: var(--required-soft); padding: 0 3px; }}
.sec.hide {{ display: none; }}
.copy-hint {{ font-size: 11.5px; color: var(--text-faint); font-family: var(--mono); margin-top: 8px; }}
</style>
</head>
<body>

<div class="app">
  <header class="top">
    <div class="top-inner">
      <div class="eyebrow"><span class="dot"></span>{html.escape(base)} · 사내용</div>
      <h1 class="title">{html.escape(title)}</h1>
      <p class="subtitle" id="summary">섹션 {len(sections)}개</p>
      <div class="search-row">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input id="searchInput" type="text" placeholder="명령어, 경로, 설정값으로 검색…" autocomplete="off">
        </div>
        <div class="result-count" id="resultCount"></div>
      </div>
      <div class="chip-row" id="chipRow"><div class="chip active" data-group="전체">전체<span class="n">{len(sections)}</span></div>{''.join(chips)}</div>
      <div class="toolbar">
        <button class="link-btn" id="revealBtn" type="button">비밀번호 표시</button>
        <button class="link-btn" id="expandAllBtn" type="button">전체 펼치기</button>
        <button class="link-btn" id="collapseAllBtn" type="button">전체 접기</button>
      </div>
    </div>
  </header>

  <div class="notice">
    이 문서에는 서버 계정·비밀번호가 포함되어 있습니다. 비밀번호는 기본적으로 흐리게 표시되며,
    이는 어깨너머 노출을 막기 위한 화면 처리일 뿐 암호화가 아닙니다. 파일 자체를 사내에서만 보관하세요.
  </div>

  <div class="list" id="list">
{chr(10).join(cards)}
  </div>
  <div class="empty-state" id="emptyState" style="display:none">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <div>일치하는 내용이 없어요.</div>
  </div>
  <div class="copy-hint">※ # 로 시작하는 명령어 줄을 클릭하면 클립보드로 복사됩니다.</div>

  <footer class="foot">{html.escape(base)} — 사내용 문서</footer>
</div>

<script>
(function () {{
  var secs = Array.prototype.slice.call(document.querySelectorAll('.card.sec'));
  var listEl = document.getElementById('list');
  var emptyEl = document.getElementById('emptyState');
  var countEl = document.getElementById('resultCount');
  var input = document.getElementById('searchInput');
  var chipRow = document.getElementById('chipRow');
  var activeGroup = '전체';

  // 원본 HTML 보관 (검색 하이라이트 후 복원용)
  secs.forEach(function (s) {{
    s.querySelector('pre.run').dataset.orig = s.querySelector('pre.run').innerHTML;
    s.classList.add('open');
  }});

  function clearMarks(pre) {{ pre.innerHTML = pre.dataset.orig; }}

  function highlight(pre, q) {{
    clearMarks(pre);
    if (!q) return 0;
    var hits = 0;
    Array.prototype.forEach.call(pre.querySelectorAll('.ln'), function (ln) {{
      var t = ln.textContent;
      var i = t.toLowerCase().indexOf(q);
      if (i === -1) return;
      hits++;
      // 텍스트 노드만 안전하게 치환
      var walker = document.createTreeWalker(ln, NodeFilter.SHOW_TEXT, null);
      var nodes = [], n;
      while ((n = walker.nextNode())) nodes.push(n);
      nodes.forEach(function (node) {{
        var s = node.nodeValue, li = s.toLowerCase().indexOf(q);
        if (li === -1) return;
        var frag = document.createDocumentFragment();
        var last = 0, k;
        while ((k = s.toLowerCase().indexOf(q, last)) !== -1) {{
          frag.appendChild(document.createTextNode(s.slice(last, k)));
          var m = document.createElement('mark');
          m.textContent = s.slice(k, k + q.length);
          frag.appendChild(m);
          last = k + q.length;
        }}
        frag.appendChild(document.createTextNode(s.slice(last)));
        node.parentNode.replaceChild(frag, node);
      }});
    }});
    return hits;
  }}

  function render() {{
    var q = input.value.trim().toLowerCase();
    var shown = 0;
    secs.forEach(function (s) {{
      var pre = s.querySelector('pre.run');
      var inGroup = activeGroup === '전체' || s.dataset.group === activeGroup;
      var hits = highlight(pre, q);
      var titleHit = q && s.querySelector('.card-name').textContent.toLowerCase().indexOf(q) !== -1;
      var visible = inGroup && (!q || hits > 0 || titleHit);
      s.classList.toggle('hide', !visible);
      if (visible) {{ shown++; if (q) s.classList.add('open'); }}
    }});
    emptyEl.style.display = shown === 0 ? '' : 'none';
    countEl.textContent = shown === secs.length ? shown + '개 섹션' : shown + ' / ' + secs.length + '개';
  }}

  input.addEventListener('input', render);

  chipRow.addEventListener('click', function (e) {{
    var chip = e.target.closest('.chip');
    if (!chip) return;
    activeGroup = chip.dataset.group;
    Array.prototype.forEach.call(chipRow.children, function (c) {{
      c.classList.toggle('active', c === chip);
    }});
    render();
  }});

  listEl.addEventListener('click', function (e) {{
    var head = e.target.closest('.card-head');
    if (head) {{
      var card = head.closest('.card.sec');
      card.classList.toggle('open');
      return;
    }}
    var cmd = e.target.closest('.ln.l-cmd');
    if (cmd) {{
      var text = cmd.textContent.replace(/^\\s*#\\s?/, '');
      var done = function () {{
        cmd.classList.add('copied');
        setTimeout(function () {{ cmd.classList.remove('copied'); }}, 600);
      }};
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(text).then(done, done);
      }} else {{
        var ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        try {{ document.execCommand('copy'); }} catch (err) {{}}
        document.body.removeChild(ta); done();
      }}
    }}
  }});

  document.getElementById('expandAllBtn').addEventListener('click', function () {{
    secs.forEach(function (s) {{ s.classList.add('open'); }});
  }});
  document.getElementById('collapseAllBtn').addEventListener('click', function () {{
    secs.forEach(function (s) {{ s.classList.remove('open'); }});
  }});

  var revealBtn = document.getElementById('revealBtn');
  revealBtn.addEventListener('click', function () {{
    var on = document.body.classList.toggle('reveal');
    revealBtn.textContent = on ? '비밀번호 숨기기' : '비밀번호 표시';
  }});

  render();
}})();
</script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"{out_path}  {os.path.getsize(out_path):,} bytes")
    print(f"  섹션 {len(sections)}개 · 가림 처리된 자격증명 {len(vault)}종")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    t = None
    for a in sys.argv[1:]:
        if a.startswith("--title="):
            t = a.split("=", 1)[1]
    build(args[0], args[1] if len(args) > 1 else None, t)
