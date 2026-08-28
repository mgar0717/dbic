(function () {
  var raw = JSON.parse(document.getElementById('table-data').textContent);
  var tables = raw.tables;
  var catOrder = raw.category_order || [];
  var schemaNote = raw.schema_note || {};

  var totalCols = tables.reduce(function (a, t) { return a + t.col_count; }, 0);

  document.getElementById('schemaLabel').textContent =
    (schemaNote.schema || 'DB') + '  ·  ' + (schemaNote.note || '');
  document.getElementById('schemaSummary').textContent =
    '테이블 ' + tables.length + '개 · 컬럼 ' + totalCols + '개';

  var catCounts = {};
  tables.forEach(function (t) { catCounts[t.category] = (catCounts[t.category] || 0) + 1; });

  var chipRow = document.getElementById('chipRow');
  var activeCat = '전체';

  function makeChip(label, count) {
    var chip = document.createElement('div');
    chip.className = 'chip' + (label === activeCat ? ' active' : '');
    chip.dataset.cat = label;
    chip.innerHTML = label + '<span class="n">' + count + '</span>';
    chip.addEventListener('click', function () {
      activeCat = label;
      Array.prototype.forEach.call(chipRow.children, function (c) {
        c.classList.toggle('active', c.dataset.cat === label);
      });
      render();
    });
    return chip;
  }
  chipRow.appendChild(makeChip('전체', tables.length));
  catOrder.forEach(function (c) {
    if (catCounts[c]) chipRow.appendChild(makeChip(c, catCounts[c]));
  });

  var listEl = document.getElementById('list');
  var emptyEl = document.getElementById('emptyState');
  var countEl = document.getElementById('resultCount');
  var searchInput = document.getElementById('searchInput');

  var openState = {};

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }

  function highlight(text, q) {
    var e = esc(text);
    if (!q) return e;
    var idx = e.toLowerCase().indexOf(q.toLowerCase());
    if (idx === -1) return e;
    return e.slice(0, idx) + '<mark>' + e.slice(idx, idx + q.length) + '</mark>' + e.slice(idx + q.length);
  }

  function nullBadge(v) {
    if (v === 'not null') return '<span class="badge req">NOT NULL</span>';
    if (v === 'null') return '<span class="badge opt">NULL</span>';
    return '<span class="badge dash">—</span>';
  }
  function keyBadge(v) {
    if (v) return '<span class="badge pk">' + esc(v) + '</span>';
    return '<span class="badge dash">—</span>';
  }

  function columnMatches(col, q) {
    if (!q) return false;
    var hay = (col.name + ' ' + col.type + ' ' + (col.desc || '')).toLowerCase();
    return hay.indexOf(q) !== -1;
  }

  function tableMatches(t, q) {
    if (!q) return true;
    if ((t.name + ' ' + (t.desc || '')).toLowerCase().indexOf(q) !== -1) return true;
    return t.columns.some(function (c) { return columnMatches(c, q); });
  }

  function renderCard(t, q) {
    var card = document.createElement('div');
    card.className = 'card';
    card.id = 'tbl-' + t.name;
    var isOpen = openState[t.name] || (!!q);
    if (isOpen) card.classList.add('open');

    var head = document.createElement('div');
    head.className = 'card-head';
    head.innerHTML =
      '<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>' +
      '<div class="card-head-main">' +
        '<div class="card-name-row">' +
          '<span class="card-name">' + highlight(t.name, q) + '</span>' +
          '<span class="card-cat">' + esc(t.category) + '</span>' +
        '</div>' +
        '<div class="card-desc">' + (t.desc ? highlight(t.desc, q) : '<span class="badge dash">설명 없음</span>') + '</div>' +
      '</div>' +
      '<div class="card-meta">' +
        (t.pk_count ? '<span class="meta-pill pk">PK ' + t.pk_count + '</span>' : '') +
        '<span class="meta-pill">컬럼 ' + t.col_count + '</span>' +
      '</div>';
    head.addEventListener('click', function () {
      var nowOpen = !card.classList.contains('open');
      card.classList.toggle('open', nowOpen);
      openState[t.name] = nowOpen;
    });
    card.appendChild(head);

    var body = document.createElement('div');
    body.className = 'card-body';
    var wrap = document.createElement('div');
    wrap.className = 'col-table-wrap';
    var rows = t.columns.map(function (c) {
      return '<tr>' +
        '<td class="col-no">' + c.no + '</td>' +
        '<td class="col-name">' + highlight(c.name, q) + '</td>' +
        '<td class="col-type">' + esc(c.type) + '</td>' +
        '<td class="col-len">' + (c.length != null ? c.length : '—') + '</td>' +
        '<td>' + keyBadge(c.key) + '</td>' +
        '<td>' + nullBadge(c.null) + '</td>' +
        '<td class="col-desc">' + (c.desc ? highlight(c.desc, q) : '<span class="badge dash">—</span>') + '</td>' +
      '</tr>';
    }).join('');
    wrap.innerHTML =
      '<table class="col-table"><thead><tr>' +
      '<th>NO</th><th>컬럼명</th><th>타입</th><th>길이</th><th>키</th><th>NULL</th><th>설명</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>';
    body.appendChild(wrap);
    card.appendChild(body);

    return card;
  }

  function render() {
    var q = searchInput.value.trim().toLowerCase();
    listEl.innerHTML = '';
    var shown = 0;
    tables.forEach(function (t) {
      if (activeCat !== '전체' && t.category !== activeCat) return;
      if (!tableMatches(t, q)) return;
      listEl.appendChild(renderCard(t, q));
      shown++;
    });
    emptyEl.style.display = shown === 0 ? '' : 'none';
    countEl.textContent = shown === tables.length ? shown + '개 테이블' : shown + ' / ' + tables.length + '개';
  }

  searchInput.addEventListener('input', render);

  document.getElementById('expandAllBtn').addEventListener('click', function () {
    tables.forEach(function (t) { openState[t.name] = true; });
    render();
  });
  document.getElementById('collapseAllBtn').addEventListener('click', function () {
    openState = {};
    render();
  });

  // #tbl-<테이블명> 으로 바로 링크했을 때 해당 카드를 펼치고 이동.
  // 필터나 검색어가 걸려 있으면 대상이 가려질 수 있으므로 먼저 초기화한다.
  function openFromHash() {
    var h = decodeURIComponent(location.hash || '').replace(/^#/, '');
    if (h.indexOf('tbl-') !== 0) return;
    var name = h.slice(4);
    if (!tables.some(function (t) { return t.name === name; })) return;

    searchInput.value = '';
    activeCat = '전체';
    Array.prototype.forEach.call(chipRow.children, function (c) {
      c.classList.toggle('active', c.dataset.cat === '전체');
    });

    openState[name] = true;
    render();
    var el = document.getElementById('tbl-' + name);
    if (el) el.scrollIntoView({ block: 'start' });
  }

  render();
  openFromHash();
  window.addEventListener('hashchange', openFromHash);
})();
