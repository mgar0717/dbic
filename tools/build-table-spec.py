#!/usr/bin/env python3
"""테이블 정의서 JSON → 자체 완결형 HTML 한 파일로 빌드.

CSS·JS·데이터·아이콘을 모두 인라인하므로 인터넷 없이 더블클릭으로 열린다.
사내 스키마 데이터는 이 저장소에 두지 않고, 빌드할 때만 외부 경로로 넘긴다.

사용법:
    python3 tools/build-table-spec.py <스키마.json> [출력.html]

입력 JSON 구조:
    {
      "schema_note":     {"schema": "...", "note": "..."},
      "category_order":  ["분류A", "분류B", ...],
      "tables": [
        {"name","desc","category","pk_count","col_count",
         "columns":[{"no","name","type","length","key","null","desc"}, ...]}
      ]
    }
"""
import json
import os
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "assets", "css", "site.scss")
JS = os.path.join(ROOT, "assets", "js", "tables.js")


def build(data_path, out_path=None):
    data = json.load(open(data_path, encoding="utf-8"))
    note = data.get("schema_note", {})
    schema = note.get("schema", "DB")
    out_path = out_path or f"{schema}-table-spec.html"

    # SCSS 의 Jekyll front matter 만 걷어내면 나머지는 순수 CSS 라 그대로 쓸 수 있다.
    css = open(CSS, encoding="utf-8").read()
    if css.lstrip().startswith("---"):
        parts = css.split("---", 2)
        css = parts[2] if len(parts) > 2 else css

    js = open(JS, encoding="utf-8").read()

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # 데이터 안의 </ 가 script 태그를 조기 종료시키지 않도록 방어
    payload = payload.replace("</", "<\\/")

    # 바로가기/탭 아이콘 (외부 파일 없이 인라인 SVG)
    icon_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#0E1513"/>'
        '<ellipse cx="32" cy="20" rx="17" ry="6.5" fill="none" stroke="#59B7A4" stroke-width="4"/>'
        '<path d="M15 20v24c0 3.6 7.6 6.5 17 6.5s17-2.9 17-6.5V20" fill="none" stroke="#59B7A4" stroke-width="4"/>'
        '<path d="M15 32c0 3.6 7.6 6.5 17 6.5s17-2.9 17-6.5" fill="none" stroke="#59B7A4" stroke-width="4"/>'
        "</svg>"
    )
    favicon = "data:image/svg+xml," + quote(icon_svg)

    html = f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0E1513">
<meta name="application-name" content="{schema} 테이블 정의서">
<title>{schema} 테이블 정의서</title>
<link rel="icon" href="{favicon}">
<link rel="apple-touch-icon" href="{favicon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
{css}
/* 단일 파일 전용 보정 */
header.top {{ padding: 18px 0 14px; }}
</style>
</head>
<body>

<div class="app">
  <header class="top">
    <div class="top-inner">
      <div class="eyebrow"><span class="dot"></span><span id="schemaLabel"></span></div>
      <h1 class="title" id="schemaName">테이블 정의서</h1>
      <p class="subtitle" id="schemaSummary"></p>
      <div class="search-row">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input id="searchInput" type="text" placeholder="테이블명, 컬럼명, 설명으로 검색…" autocomplete="off">
        </div>
        <div class="result-count" id="resultCount"></div>
      </div>
      <div class="chip-row" id="chipRow"></div>
      <div class="toolbar">
        <button class="link-btn" id="expandAllBtn" type="button">전체 펼치기</button>
        <button class="link-btn" id="collapseAllBtn" type="button">전체 접기</button>
      </div>
    </div>
  </header>

  <main class="list" id="list"></main>
  <div class="empty-state" id="emptyState" style="display:none">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <div>일치하는 테이블이 없어요.</div>
  </div>

  <footer class="foot">{schema} {note.get('note', '')} — 사내용 문서</footer>
</div>

<script id="table-data" type="application/json">{payload}</script>
<script>
{js}
</script>
</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    cols = sum(t.get("col_count", 0) for t in data["tables"])
    print(f"{out_path}  {os.path.getsize(out_path):,} bytes")
    print(f"  스키마 {schema} · 테이블 {len(data['tables'])}개 · 컬럼 {cols}개")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
