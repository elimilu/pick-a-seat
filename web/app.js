const byId = id => document.getElementById(id);
const show = byId('show'), map = byId('map'), view = byId('view');
let concerts, inventory = [], selected = new Set(), request;

const sections = ['Front floor', 'Rear floor', 'Lower west', 'Lower east', 'Lower north', 'Upper west', 'Upper east', 'Upper north'];
const prefixes = ['', 'RF-', 'LW-', 'LE-', 'LN-', 'UW-', 'UE-', 'UN-'];
const rowsPerSection = 50;

function rowName(n) {
  let s = '';
  while (n) { n--; s = String.fromCharCode(65 + n % 26) + s; n = Math.floor(n / 26); }
  return s;
}

function renderSelection() {
  byId('count').textContent = selected.size;
  byId('picks').textContent = selected.size ? [...selected].join(' · ') : 'Tap an available seat to select it.';
}

function renderMap() {
  const fragment = document.createDocumentFragment();
  let row, lastRow, label, prefix;
  for (const [r, number, booked] of inventory) {
    if (lastRow !== r) {
      row = document.createElement('div'); row.className = 'row';
      const section = Math.floor((r - 1) / rowsPerSection);
      prefix = prefixes[section]; label = rowName((r - 1) % rowsPerSection + 1); lastRow = r;
      if ((r - 1) % rowsPerSection === 0) {
        const heading = document.createElement('h3'); heading.className = 'section-label';
        heading.textContent = sections[section]; fragment.append(heading);
      }
      const name = document.createElement('span'); name.className = 'row-label'; name.textContent = label;
      row.append(name); fragment.append(row);
    }
    const id = prefix + label + number, button = document.createElement('button');
    button.type = 'button'; button.className = 'seat'; button.textContent = number;
    button.dataset.seat = id; button.disabled = Boolean(booked);
    button.setAttribute('aria-label', `Seat ${id}${booked ? ', booked' : ''}`);
    button.setAttribute('aria-pressed', String(selected.has(id)));
    row.append(button);
  }
  map.replaceChildren(fragment);
}

map.addEventListener('click', event => {
  const button = event.target.closest('button[data-seat]');
  if (!button || button.disabled) return;
  const id = button.dataset.seat;
  if (selected.has(id)) selected.delete(id); else selected.add(id);
  button.setAttribute('aria-pressed', String(selected.has(id)));
  renderSelection();
  button.focus({preventScroll:true});
});

async function loadShow() {
  request?.abort();
  const controller = new AbortController(); request = controller;
  const concert = concerts.find(s => s.id === Number(show.value));
  selected = new Set(); inventory = []; map.replaceChildren(); renderSelection();
  byId('act').textContent = concert.title;
  byId('date').textContent = new Intl.DateTimeFormat('en-US', {dateStyle:'full',timeZone:'UTC'}).format(new Date(concert.night+'T12:00:00Z'));
  byId('status').textContent = 'Loading seat map…';
  try {
    const response = await fetch(`/api/shows/${concert.id}/seats`, {signal:controller.signal});
    if (!response.ok) throw new Error();
    const rows = await response.json();
    if (controller.signal.aborted) return;
    inventory = rows; renderMap(); view.scrollTo(0,0); byId('status').textContent = '';
  } catch (error) {
    if (error.name !== 'AbortError') byId('status').textContent = 'Could not load seats. Switch shows to retry.';
  }
}

try {
  const response = await fetch('/api/shows');
  if (!response.ok) throw new Error();
  concerts = await response.json();
  show.replaceChildren(...concerts.map(s => new Option(s.title, s.id))); show.disabled = false;
  show.addEventListener('change', loadShow); await loadShow();
} catch { byId('status').textContent = 'Could not load shows. Refresh to retry.'; }
