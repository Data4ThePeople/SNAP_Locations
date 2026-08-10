/* SNAP retailer map.
 *
 * One row per store carrying a 20-bit year mask, so the year slider and every
 * filter run client-side over typed arrays. No server, no per-year datasets.
 *
 * Palette note: this is an all-pairs chart form (any two dots can be adjacent),
 * where the validated categorical palette carries at most THREE slots. Formats
 * therefore act as a filter, not a color dimension; when coloring by format the
 * user highlights up to 3 and the rest fall back to a non-identity gray.
 */

const THEME = {
  dark: {
    tiles: 'dark_all',
    // Validated all-pairs on #0e0e0e: CVD dE 9.4, normal-vision dE 20.9.
    slots: [[57, 135, 229], [217, 89, 38], [25, 158, 112]],
    other: [92, 92, 88],
  },
  light: {
    tiles: 'light_all',
    // Validated all-pairs on #fafaf8: CVD dE 9.2, normal-vision dE 24.0.
    slots: [[42, 120, 214], [235, 104, 52], [27, 175, 122]],
    other: [176, 175, 170],
  },
};

const hex = (c) => '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');
const fmtNum = (n) => n.toLocaleString('en-US');

const state = {
  yearIndex: 19,
  theme: 'dark',
  colorMode: 'ownership',
  highlight: [],       // format indices, max 3, kept in meta.formats order
  formatOn: null,      // Uint8Array
  brandOn: null,       // Uint8Array, index 0 unused
  unbranded: [0, 1, 1], // by ownership id: [chain(unused), independent, unknown]
  slots: [null, null, null], // each: {type:'group'|'brand', id} or null
  onlySlots: false,
  dotSize: 1.6,
  region: 'conus',
  userMoved: false,
  visible: 0,
};

/** Which color slot (0-2) this store occupies, or -1. First match wins. */
function slotOf(i) {
  const y = state.yearIndex;
  for (let s = 0; s < 3; s++) {
    const ref = state.slots[s];
    if (!ref) continue;
    if (ref.type === 'brand') {
      if (brandId[i] === ref.id) return s;
    } else if (groupId[i] === ref.id && y >= groupFrom[i] && y <= groupUntil[i]) {
      return s;
    }
  }
  return -1;
}

let meta, N, position, formatId, ownershipId, brandId, yearMask, filterValue, colors, deckgl;
let groupId, groupFrom, groupUntil;

// ---------------------------------------------------------------- load

/** Inflate the gzip+base64 payload the standalone build embeds. */
async function inflate(b64) {
  if (typeof DecompressionStream === 'undefined') {
    throw new Error('This browser has no DecompressionStream; run the served version instead.');
  }
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Response(stream).arrayBuffer();
}

/** Embedded payload when running as a single file, fetched otherwise. */
async function loadPayload() {
  if (window.__SNAP__) {
    return [window.__SNAP__.meta, await inflate(window.__SNAP__.points)];
  }
  return Promise.all([
    fetch('data/meta.json').then((r) => r.json()),
    fetch('data/points.bin').then((r) => r.arrayBuffer()),
  ]);
}

async function load() {
  const [m, buf] = await loadPayload();
  meta = m;
  N = meta.count;

  // Section order guarantees alignment for any N: 10N is always even (Uint16)
  // and 12N always divisible by 4 (Uint32).
  position = new Float32Array(buf, 0, N * 2);
  formatId = new Uint8Array(buf, N * 8, N);
  ownershipId = new Uint8Array(buf, N * 9, N);
  brandId = new Uint16Array(buf, N * 10, N);
  yearMask = new Uint32Array(buf, N * 12, N);
  // Group membership is year-bounded: Harris Teeter is Kroger only from 2014,
  // and Kroger's convenience banners only through 2017.
  groupId = new Uint8Array(buf, N * 16, N);
  groupFrom = new Uint8Array(buf, N * 17, N);
  groupUntil = new Uint8Array(buf, N * 18, N);

  filterValue = new Float32Array(N);
  colors = new Uint8Array(N * 3);

  state.formatOn = new Uint8Array(meta.formats.length).fill(1);
  state.brandOn = new Uint8Array(meta.brands.length + 1).fill(1);
  document.getElementById('brandSearch').placeholder =
    `Search ${meta.brands.length} retailers…`;

  selfCheck();
  buildFormatList();
  buildBrandList();
  buildSlotPickers();
  wireControls();
  initDeck();
  refresh(true);
  document.getElementById('loading').remove();
}

/** Verify the decoded binary reproduces the counts the exporter asserted. */
function selfCheck() {
  for (const [year, expected] of Object.entries(meta.per_year_totals)) {
    const bit = 1 << (Number(year) - meta.years[0]);
    let n = 0;
    for (let i = 0; i < N; i++) if (yearMask[i] & bit) n++;
    if (n !== expected) {
      console.error(`Year ${year}: decoded ${n} but meta says ${expected}`);
      return;
    }
  }
  console.info(`Self-check OK — all ${meta.years.length} years match meta.per_year_totals.`);
}

// ---------------------------------------------------------------- filtering

function recompute() {
  const bit = 1 << state.yearIndex;
  const { formatOn, brandOn, unbranded } = state;
  let visible = 0;
  for (let i = 0; i < N; i++) {
    let v = 0;
    if ((yearMask[i] & bit) !== 0 && formatOn[formatId[i]]) {
      const b = brandId[i];
      v = b === 0 ? unbranded[ownershipId[i]] : brandOn[b];
      if (v && state.onlySlots && state.colorMode === 'group' && slotOf(i) < 0) v = 0;
    }
    filterValue[i] = v;
    visible += v;
  }
  state.visible = visible;
}

function recolor() {
  const t = THEME[state.theme];
  const other = t.other;
  // Slot per format index, only in format mode; -1 means "not highlighted".
  const fmtSlot = new Int8Array(meta.formats.length).fill(-1);
  if (state.colorMode === 'format') {
    state.highlight.forEach((fi, k) => { fmtSlot[fi] = k; });
  }
  for (let i = 0; i < N; i++) {
    let c;
    if (state.colorMode === 'ownership') {
      const o = ownershipId[i];
      c = o === 0 ? t.slots[0] : o === 1 ? t.slots[1] : other;
    } else if (state.colorMode === 'format') {
      const s = fmtSlot[formatId[i]];
      c = s >= 0 ? t.slots[s] : other;
    } else if (state.colorMode === 'group') {
      const s = slotOf(i);
      c = s >= 0 ? t.slots[s] : other;
    } else {
      c = t.slots[0];
    }
    colors[i * 3] = c[0];
    colors[i * 3 + 1] = c[1];
    colors[i * 3 + 2] = c[2];
  }
}

// ---------------------------------------------------------------- deck

// Alaska, Hawaii and the territories are all in the data and on the basemap —
// they just sit outside a lower-48 viewport, so they need a way to be reached.
// Stored as bounds, not a fixed center and zoom: the map sits between two
// panels, so its aspect ratio depends on the window and a hardcoded zoom either
// clips the coasts or strands the country in empty ocean.
const REGIONS = {
  conus: [[-124.8, 24.4], [-66.9, 49.4]],
  ak: [[-172.5, 51.0], [-129.5, 71.5]],
  hi: [[-160.3, 18.8], [-154.7, 22.3]],
  vi: [[-65.15, 17.6], [-64.5, 18.5]],
  pac: [[144.55, 13.2], [145.05, 13.7]],
};

function viewFor(key) {
  const el = document.getElementById('map');
  const width = Math.max(el.clientWidth || 800, 120);
  const height = Math.max(el.clientHeight || 600, 120);
  const padding = Math.max(12, Math.min(40, Math.min(width, height) * 0.05));
  const { longitude, latitude, zoom } =
    new deck.WebMercatorViewport({ width, height }).fitBounds(REGIONS[key], { padding });
  return { longitude, latitude, zoom, minZoom: 1, maxZoom: 16 };
}

function initDeck() {
  deckgl = new deck.Deck({
    parent: document.getElementById('map'),
    initialViewState: viewFor('conus'),
    controller: true,
    layers: [],
    onHover: showTooltip,
    // Once the user pans or zooms, stop refitting on resize — their view wins.
    onViewStateChange: ({ interactionState }) => {
      if (interactionState && (interactionState.isDragging || interactionState.isZooming)) {
        state.userMoved = true;
      }
    },
  });

  let t = null;
  addEventListener('resize', () => {
    clearTimeout(t);
    t = setTimeout(() => {
      if (!state.userMoved) deckgl.setProps({ initialViewState: viewFor(state.region) });
    }, 150);
  });
}

function flyTo(key) {
  state.region = key;
  state.userMoved = false;
  deckgl.setProps({
    initialViewState: {
      ...viewFor(key),
      transitionDuration: 900,
      transitionInterpolator: new deck.FlyToInterpolator(),
    },
  });
}

function basemapLayer() {
  const style = THEME[state.theme].tiles;
  return new deck.TileLayer({
    id: `base-${style}`,
    data: `https://basemaps.cartocdn.com/rastertiles/${style}/{z}/{x}/{y}${devicePixelRatio > 1 ? '@2x' : ''}.png`,
    minZoom: 0,
    maxZoom: 19,
    tileSize: 256,
    renderSubLayers: (props) => {
      // deck.gl v9 renamed tile.bbox -> tile.boundingBox ([[w,s],[e,n]]);
      // accept either so a minor version bump doesn't blank the basemap.
      const t = props.tile;
      const bounds = t.boundingBox
        ? [t.boundingBox[0][0], t.boundingBox[0][1], t.boundingBox[1][0], t.boundingBox[1][1]]
        : [t.bbox.west, t.bbox.south, t.bbox.east, t.bbox.north];
      return new deck.BitmapLayer(props, { data: null, image: props.data, bounds });
    },
  });
}

let dataVersion = 0;
function pointLayer() {
  // A fresh data object each refresh so deck re-uploads the mutated buffers.
  return new deck.ScatterplotLayer({
    id: 'stores',
    data: {
      length: N,
      attributes: {
        getPosition: { value: position, size: 2 },
        getFillColor: { value: colors, size: 3, normalized: true },
        getFilterValue: { value: filterValue, size: 1 },
      },
    },
    dataComparator: () => false,
    _dataDiff: () => [{ startRow: 0, endRow: N }],
    radiusUnits: 'meters',
    getRadius: 110,
    radiusScale: state.dotSize,
    radiusMinPixels: 1.5 * state.dotSize,
    // Capped low, dots stayed pinpricks however far you zoomed in.
    radiusMaxPixels: 44,
    opacity: 0.85,
    pickable: true,
    extensions: [new deck.DataFilterExtension({ filterSize: 1 })],
    filterRange: [0.5, 1.5],
    updateTriggers: { getFillColor: dataVersion, getFilterValue: dataVersion },
  });
}

function refresh(recolorToo) {
  recompute();
  if (recolorToo) recolor();
  dataVersion++;
  deckgl.setProps({ layers: [basemapLayer(), pointLayer()] });
  renderCount();
  syncOwnershipYears();
  renderPanelCounts();
}

// ---------------------------------------------------------------- tooltip

function showTooltip({ index, x, y }) {
  const el = document.getElementById('tooltip');
  if (index < 0 || filterValue[index] === 0) { el.hidden = true; return; }
  const b = brandId[index];
  const brand = b === 0 ? null : meta.brands[b - 1].name;
  el.innerHTML =
    `<b>${brand || 'Independent / unbranded'}</b>` +
    `<span>${meta.formats[formatId[index]]}<br>` +
    `${meta.ownership[ownershipId[index]]}</span>`;
  el.hidden = false;
  el.style.left = Math.min(x + 14, innerWidth - 245) + 'px';
  el.style.top = (y + 14) + 'px';
}

// ---------------------------------------------------------------- UI

function renderCount() {
  const year = meta.years[state.yearIndex];
  const total = meta.per_year_totals[year];
  document.getElementById('yearOut').textContent = year;
  document.getElementById('count').innerHTML =
    `Showing <strong>${fmtNum(state.visible)}</strong> of ${fmtNum(total)} stores`;
}

function renderLegend() {
  const t = THEME[state.theme];
  const box = document.getElementById('legend');
  const hint = document.getElementById('highlightHint');
  let items = [];
  if (state.colorMode === 'ownership') {
    items = [['Chain', t.slots[0]], ['Independent', t.slots[1]], ['Unknown', t.other]];
  } else if (state.colorMode === 'format') {
    items = state.highlight.map((fi, k) => [meta.formats[fi], t.slots[k]]);
    if (items.length < 3) items.push(['Other formats', t.other]);
  } else if (state.colorMode === 'group') {
    items = state.slots
      .map((ref, k) => (ref ? [labelOf(ref), t.slots[k]] : null))
      .filter(Boolean);
    if (!state.onlySlots) items.push(['Everything else', t.other]);
  }
  hint.hidden = state.colorMode !== 'format';
  document.getElementById('slots').hidden = state.colorMode !== 'group';
  box.innerHTML = items
    .map(([label, c]) => `<div><i style="background:${hex(c)}"></i>${label}</div>`)
    .join('');
}

function labelOf(ref) {
  return ref.type === 'group' ? meta.groups[ref.id - 1].name : meta.brands[ref.id - 1].name;
}

function buildSlotPickers() {
  const opts =
    '<option value="">— none —</option>' +
    '<optgroup label="Parent companies">' +
    meta.groups.map((g, i) =>
      `<option value="group:${i + 1}">${g.name} (${fmtNum(g.total)})</option>`).join('') +
    '</optgroup><optgroup label="Individual retailers">' +
    meta.brands.map((b, i) =>
      `<option value="brand:${i + 1}">${b.name} (${fmtNum(b.total)})</option>`).join('') +
    '</optgroup>';

  document.querySelectorAll('#slots select').forEach((sel) => {
    sel.innerHTML = opts;
    sel.addEventListener('change', () => {
      const k = +sel.dataset.slot;
      const v = sel.value;
      state.slots[k] = v ? { type: v.split(':')[0], id: +v.split(':')[1] } : null;
      paintSwatches();
      renderLegend();
      refresh(true);
    });
  });

  document.getElementById('onlySlots').addEventListener('change', (e) => {
    state.onlySlots = e.target.checked;
    renderLegend();
    refresh(true);
  });
}

function paintSwatches() {
  const t = THEME[state.theme];
  document.querySelectorAll('#slots [data-swatch]').forEach((el) => {
    const k = +el.dataset.swatch;
    el.style.background = state.slots[k] ? hex(t.slots[k]) : 'transparent';
    el.style.borderColor = state.slots[k] ? 'transparent' : 'var(--line)';
  });
}

function setSlot(k, ref) {
  state.slots[k] = ref;
  const sel = document.querySelector(`#slots select[data-slot="${k}"]`);
  if (sel) sel.value = ref ? `${ref.type}:${ref.id}` : '';
}

function buildFormatList() {
  const box = document.getElementById('formats');
  box.innerHTML = meta.formats.map((f, i) => `
    <label class="item">
      <input type="checkbox" data-fmt="${i}" checked>
      <span class="nm">${f}</span>
      <button class="hl" data-hlfmt="${i}" title="Highlight this format" hidden></button>
    </label>`).join('');

  box.addEventListener('change', (e) => {
    const i = e.target.dataset.fmt;
    if (i === undefined) return;
    state.formatOn[i] = e.target.checked ? 1 : 0;
    refresh(false);
  });
  box.addEventListener('click', (e) => {
    const i = e.target.dataset.hlfmt;
    if (i === undefined) return;
    e.preventDefault();
    toggleHighlight(Number(i));
  });
}

function toggleHighlight(fi) {
  const at = state.highlight.indexOf(fi);
  if (at >= 0) state.highlight.splice(at, 1);
  else {
    if (state.highlight.length >= 3) state.highlight.shift();
    state.highlight.push(fi);
    // Keep a fixed order so colors follow the format, not the click sequence.
    state.highlight.sort((a, b) => a - b);
  }
  paintHighlightButtons();
  renderLegend();
  refresh(true);
}

function paintHighlightButtons() {
  const t = THEME[state.theme];
  const show = state.colorMode === 'format';
  document.querySelectorAll('[data-hlfmt]').forEach((btn) => {
    btn.hidden = !show;
    const k = state.highlight.indexOf(Number(btn.dataset.hlfmt));
    if (k >= 0) {
      btn.style.background = hex(t.slots[k]);
      btn.dataset.slot = k;
    } else {
      btn.style.background = '';
      delete btn.dataset.slot;
    }
  });
}

const CATEGORY_LABEL = {
  grocery: 'Supermarkets & grocery', mass: 'Mass merchants', club: 'Warehouse clubs',
  dollar: 'Dollar stores', drug: 'Drug stores', convenience: 'Convenience chains',
  variety: 'Variety & closeout', specialty: 'Specialty & delivery',
};

/** Rewrite every count in the retailer panel for the selected year.
 *
 * These used to be all-time totals sitting next to a year-filtered map, which
 * read as a mismatch: 311,131 independents beside 88,229 shown on screen.
 */
function renderPanelCounts() {
  const y = state.yearIndex;
  document.querySelectorAll('[data-count]').forEach((el) => {
    const [kind, key] = el.dataset.count.split(':');
    let n;
    if (kind === 'brand') n = meta.brands[+key - 1].by_year[y];
    else if (kind === 'group') n = meta.groups[+key].by_year[y];
    else n = meta.unbranded[`${key}_by_year`][y];
    el.textContent = fmtNum(n);
    el.classList.toggle('zero', n === 0);
  });
}

/** Dim banners that the selected year puts outside their parent's ownership. */
function syncOwnershipYears() {
  const y = state.yearIndex;
  document.querySelectorAll('.item.child[data-from]').forEach((el) => {
    el.classList.toggle('out', y < +el.dataset.from || y > +el.dataset.until);
  });
}

/** Recompute each parent row's checkbox from its members: on / off / mixed. */
function syncParents() {
  document.querySelectorAll('[data-parent]').forEach((cb) => {
    const ids = cb.dataset.parent.split(',').map(Number);
    const on = ids.filter((id) => state.brandOn[id]).length;
    cb.checked = on > 0;
    cb.indeterminate = on > 0 && on < ids.length;
  });
}

function buildBrandList() {
  const box = document.getElementById('brands');
  const byName = new Map(meta.brands.map((b, i) => [b.name, { ...b, id: i + 1 }]));

  // A brand can sit under two parents — Tom Thumb is Kroger in FL/AL and
  // Albertsons in TX — but it is one filterable brand, so it is listed once
  // under the first parent and marked.
  const parentsOf = new Map();
  meta.groups.forEach((g) => g.members.forEach((m) => {
    if (!parentsOf.has(m.brand)) parentsOf.set(m.brand, []);
    if (!parentsOf.get(m.brand).includes(g.name)) parentsOf.get(m.brand).push(g.name);
  }));

  // These carry data-name like every other row so the search filter hides them
  // too; without it they sat pinned above the results looking like matches.
  let html = `
    <div class="group">Unbranded</div>
    <label class="item" data-name="independent unbranded"><input type="checkbox" data-unb="1" checked>
      <span class="nm">Independent (unbranded)</span>
      <span class="n" data-count="unb:independent"></span></label>
    <label class="item" data-name="unknown"><input type="checkbox" data-unb="2" checked>
      <span class="nm">Unknown</span>
      <span class="n" data-count="unb:unknown"></span></label>
    <div class="group">Parent companies</div>`;

  const claimed = new Set();
  for (const g of [...meta.groups].sort((a, b) => b.total - a.total)) {
    const members = [...new Map(
      g.members.map((m) => byName.get(m.brand)).filter(Boolean).map((m) => [m.id, m])
    ).values()].filter((m) => !claimed.has(m.id));
    if (!members.length) continue;
    members.sort((a, b) => b.total - a.total);

    const ids = members.map((m) => m.id);
    const names = [g.name, ...members.map((m) => m.name)].join(' ').toLowerCase();
    html += `
      <label class="item parent" data-name="${names}">
        <input type="checkbox" data-parent="${ids}" checked>
        <span class="nm">${g.name}</span>
        <span class="n" data-count="group:${meta.groups.indexOf(g)}"></span>
      </label>`;
    for (const m of members) {
      claimed.add(m.id);
      const also = (parentsOf.get(m.name) || []).filter((p) => p !== g.name);
      // Ownership moves: Harris Teeter joins Kroger in 2014, Quik Stop leaves
      // after 2017. Carry the window so the row can dim when the selected year
      // falls outside it.
      const rule = g.members.find((x) => x.brand === m.name) || {};
      const y0 = meta.years[0];
      const bounded = rule.from > y0 || rule.until < meta.years[meta.years.length - 1];
      const range = rule.from > y0 && rule.until < meta.years[meta.years.length - 1]
        ? `${rule.from}–${rule.until}`
        : rule.from > y0 ? `from ${rule.from}` : `to ${rule.until}`;
      html += `
        <label class="item child" data-name="${m.name.toLowerCase()}"
               data-from="${rule.from - y0}" data-until="${rule.until - y0}"
               ${also.length ? `title="Also part of ${also.join(', ')}"` : ''}>
          <input type="checkbox" data-brand="${m.id}" checked>
          <span class="nm">${m.name}${also.length ? ' †' : ''}</span>
          ${bounded ? `<span class="yr">${range}</span>` : ''}
          <span class="n" data-count="brand:${m.id}"></span>
        </label>`;
    }
  }

  // Everything with no parent company, still grouped by what kind of store it is.
  const rest = {};
  meta.brands.forEach((b, i) => {
    if (!claimed.has(i + 1)) (rest[b.category] ||= []).push({ ...b, id: i + 1 });
  });
  for (const cat of Object.keys(CATEGORY_LABEL)) {
    const list = rest[cat];
    if (!list) continue;
    list.sort((a, b) => b.total - a.total);
    html += `<div class="group">${CATEGORY_LABEL[cat]}</div>` + list.map((b) => `
      <label class="item" data-name="${b.name.toLowerCase()}">
        <input type="checkbox" data-brand="${b.id}" checked>
        <span class="nm">${b.name}</span>
        <span class="n" data-count="brand:${b.id}"></span>
      </label>`).join('');
  }
  box.innerHTML = html;

  box.addEventListener('change', (e) => {
    const { brand, unb, parent } = e.target.dataset;
    if (parent !== undefined) {
      const on = e.target.checked ? 1 : 0;
      parent.split(',').forEach((id) => {
        state.brandOn[id] = on;
        const cb = box.querySelector(`[data-brand="${id}"]`);
        if (cb) cb.checked = !!on;
      });
    } else if (brand !== undefined) {
      state.brandOn[brand] = e.target.checked ? 1 : 0;
      syncParents();
    } else if (unb !== undefined) {
      state.unbranded[unb] = e.target.checked ? 1 : 0;
    } else return;
    refresh(false);
  });

  document.getElementById('brandSearch').addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    // A parent row's data-name includes its members, so searching "kroger"
    // matches the parent; its children are then revealed with it.
    let parentShown = false;
    box.querySelectorAll('.item[data-name]').forEach((el) => {
      let show;
      if (!q) show = true;
      else if (el.classList.contains('parent')) {
        show = el.dataset.name.includes(q);
        parentShown = show;
      } else if (el.classList.contains('child')) {
        show = parentShown || el.dataset.name.includes(q);
      } else show = el.dataset.name.includes(q);
      el.style.display = show ? '' : 'none';
    });
    box.querySelectorAll('.group').forEach((g) => { g.style.display = q ? 'none' : ''; });
  });
}

function setAll(kind, on) {
  if (kind === 'format') {
    state.formatOn.fill(on);
    document.querySelectorAll('[data-fmt]').forEach((c) => (c.checked = !!on));
  } else {
    state.brandOn.fill(on);
    state.unbranded[1] = state.unbranded[2] = on;
    document.querySelectorAll('[data-brand],[data-unb]').forEach((c) => (c.checked = !!on));
    document.querySelectorAll('[data-parent]').forEach((c) => {
      c.checked = !!on;
      c.indeterminate = false;
    });
  }
  refresh(false);
}

function wireControls() {
  document.getElementById('year').addEventListener('input', (e) => {
    state.yearIndex = +e.target.value;
    // Group membership is year-dependent, so colors move with the slider.
    refresh(state.colorMode === 'group');
  });

  document.getElementById('regions').addEventListener('click', (e) => {
    if (e.target.dataset.region) flyTo(e.target.dataset.region);
  });

  document.getElementById('dotSize').addEventListener('input', (e) => {
    state.dotSize = +e.target.value;
    dataVersion++;
    deckgl.setProps({ layers: [basemapLayer(), pointLayer()] });
  });

  document.getElementById('colorMode').addEventListener('click', (e) => {
    const mode = e.target.dataset.mode;
    if (!mode) return;
    state.colorMode = mode;
    document.querySelectorAll('#colorMode button')
      .forEach((b) => b.classList.toggle('on', b.dataset.mode === mode));
    if (mode === 'group' && !state.slots.some(Boolean)) {
      // Seed with the comparison that motivated this mode.
      const gi = (name) => meta.groups.findIndex((g) => g.name === name) + 1;
      if (gi('Kroger')) setSlot(0, { type: 'group', id: gi('Kroger') });
      if (gi('Giant Eagle')) setSlot(1, { type: 'group', id: gi('Giant Eagle') });
      paintSwatches();
    }
    if (mode === 'format' && !state.highlight.length) {
      // Seed with the formats this project is actually about.
      ['Supermarket', 'Grocery (Large)', 'Dollar Store']
        .map((f) => meta.formats.indexOf(f))
        .filter((i) => i >= 0)
        .forEach((i) => state.highlight.push(i));
      state.highlight.sort((a, b) => a - b);
    }
    paintHighlightButtons();
    renderLegend();
    refresh(true);
  });

  document.querySelectorAll('[data-all]').forEach((b) =>
    b.addEventListener('click', () => setAll(b.dataset.all, 1)));
  document.querySelectorAll('[data-none]').forEach((b) =>
    b.addEventListener('click', () => setAll(b.dataset.none, 0)));

  document.getElementById('light').addEventListener('change', (e) => {
    state.theme = e.target.checked ? 'light' : 'dark';
    document.documentElement.style.background = state.theme === 'light' ? '#fafaf8' : '#0e0e0e';
    paintHighlightButtons();
    paintSwatches();
    renderLegend();
    refresh(true);
  });

  let timer = null;
  document.getElementById('play').addEventListener('click', (e) => {
    if (timer) {
      clearInterval(timer); timer = null; e.target.textContent = '▶';
      return;
    }
    e.target.textContent = '❚❚';
    timer = setInterval(() => {
      state.yearIndex = (state.yearIndex + 1) % meta.years.length;
      document.getElementById('year').value = state.yearIndex;
      refresh(state.colorMode === 'group');
    }, 750);
  });

  renderLegend();
}

load().catch((err) => {
  document.getElementById('loading').textContent = 'Failed to load: ' + err.message;
  console.error(err);
});
