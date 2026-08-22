/* ═══════════════════════════════════════════════════════════════════════
   SafeWalk — app.js
   State management, API calls, Leaflet map, tab switching, interactions
   ═══════════════════════════════════════════════════════════════════════ */

const API = '';  // Same-origin, Flask serves both

// ── State ─────────────────────────────────────────────────────────────
const state = {
  city: 'Dehradun',
  country: 'India',
  hour: 22,
  landmarks: [],
  sessionId: 'user_' + Math.random().toString(36).slice(2, 10),
  votedIds: new Set(),
  routeLayers: [],
};

// ── DOM refs ──────────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ── Map ───────────────────────────────────────────────────────────────
let map;

function initMap() {
  map = L.map('map', { zoomControl: true }).setView([30.3243, 78.0419], 13);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CartoDB',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(map);
}

function clearRouteLayers() {
  state.routeLayers.forEach(l => map.removeLayer(l));
  state.routeLayers = [];
}

function drawRoutes(safest, fastest) {
  clearRouteLayers();

  if (safest?.points?.length) {
    const safeLine = L.polyline(safest.points, {
      color: '#059669', weight: 7, opacity: 0.9,
    }).addTo(map).bindTooltip(`Safest Route · Safety: ${safest.safety_avg}/100`);
    state.routeLayers.push(safeLine);

    // Start & end markers
    const startMarker = L.circleMarker(safest.points[0], {
      radius: 10, fillColor: '#4F46E5', fillOpacity: 1, color: '#fff', weight: 3,
    }).addTo(map).bindTooltip('Start');
    const endMarker = L.circleMarker(safest.points[safest.points.length - 1], {
      radius: 10, fillColor: '#E11D48', fillOpacity: 1, color: '#fff', weight: 3,
    }).addTo(map).bindTooltip('Destination');
    state.routeLayers.push(startMarker, endMarker);

    // Danger zone markers
    (safest.danger_zones || []).forEach(dz => {
      const m = L.circleMarker(dz, {
        radius: 8, fillColor: '#E11D48', fillOpacity: 0.6, color: '#fff', weight: 2,
      }).addTo(map).bindTooltip('Danger Zone');
      state.routeLayers.push(m);
    });
  }

  if (fastest?.points?.length) {
    const fastLine = L.polyline(fastest.points, {
      color: '#E11D48', weight: 5, opacity: 0.7, dashArray: '10 8',
    }).addTo(map).bindTooltip(`Fastest Route · ${fastest.duration_min} mins`);
    state.routeLayers.push(fastLine);
  }

  // Fit bounds
  if (safest?.points?.length) {
    map.fitBounds(L.latLngBounds(safest.points), { padding: [30, 30] });
  }
}

// ── Toast ─────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  $('#toastContainer').appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 400); }, 3500);
}

// ── Loading ───────────────────────────────────────────────────────────
function showLoading(text = 'Loading...') {
  $('#loadingText').textContent = text;
  $('#loadingOverlay').style.display = 'flex';
}
function hideLoading() {
  $('#loadingOverlay').style.display = 'none';
}

// ── API helpers ───────────────────────────────────────────────────────
async function apiGet(path) {
  const res = await fetch(`${API}${path}`);
  return res.json();
}
async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ── Landmarks / Chips ─────────────────────────────────────────────────
async function loadLandmarks() {
  const data = await apiGet(`/api/landmarks?city=${encodeURIComponent(state.city)}`);
  state.landmarks = data.landmarks || [];
  renderChips();
  if (state.landmarks.length >= 2) {
    $('#startInput').value = state.landmarks[0];
    $('#endInput').value = state.landmarks[1];
  }
}

function shortenLabel(label) {
  return label.split(',')[0]
    .replace('Bandra Kurla Complex (BKC)', 'BKC')
    .replace('Andheri West Metro Station', 'Andheri Metro')
    .replace('Forest Research Institute (FRI)', 'FRI Institute')
    .replace('Rajiv Chowk Metro Station Exit 2', 'Rajiv Chowk Metro')
    .replace('UPES Bidholi Campus', 'UPES Bidholi')
    .replace('UPES Kandoli Campus', 'UPES Kandoli')
    .replace('Chennai Central Railway Station', 'Chennai Central')
    .replace('Howrah Railway Station', 'Howrah Station')
    .replace('Washington Square Park, Greenwich Village', 'Washington Square');
}

function renderChips() {
  const row = $('#chipsRow');
  row.innerHTML = '';
  state.landmarks.slice(0, 5).forEach((lm, i) => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.textContent = shortenLabel(lm);
    chip.title = lm;
    chip.style.animationDelay = `${i * 0.06}s`;
    chip.addEventListener('click', () => {
      $('#endInput').value = lm;
      $$('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
    });
    row.appendChild(chip);
  });
  $('#suggestionsTitle').textContent = `Quick Destination Suggestions for ${state.city}:`;
}

// ── City Switch ───────────────────────────────────────────────────────
async function setCity() {
  const custom = $('#customCity').value.trim();
  state.city = custom || $('#citySelect').value;
  $('#customCity').value = '';
  showLoading(`Switching to ${state.city}...`);
  try {
    await loadLandmarks();
    const statsData = await apiGet(`/api/stats?city=${encodeURIComponent(state.city)}`);
    state.country = 'India'; // Default, could be enhanced
    $('#cityBadge').textContent = `📍 ${state.city}`;
    $('#mainSubtitle').innerHTML = `Real-time crowdsourced safety routes &amp; Gemini AI guidance for <strong>${state.city}</strong>`;
    clearRouteLayers();
    toast(`City set to ${state.city}`, 'success');
  } catch (e) {
    toast('Failed to switch city', 'error');
  }
  hideLoading();
}

// ── Hour Slider ───────────────────────────────────────────────────────
function updateHourLabel() {
  const h = parseInt($('#hourSlider').value);
  state.hour = h;
  const icon = (h >= 20 || h < 6) ? '🌙' : '☀️';
  const period = (h >= 20 || h < 6) ? 'Night' : 'Day';
  $('#hourLabel').textContent = `${String(h).padStart(2, '0')}:00 ${icon} ${period}`;
}

// ── Route Planning ────────────────────────────────────────────────────
async function findRoute() {
  const start = $('#startInput').value.trim();
  const end = $('#endInput').value.trim();
  if (!start || !end) { toast('Enter start and destination', 'error'); return; }

  showLoading(`Calculating safest route in ${state.city}...`);
  try {
    const res = await apiPost('/api/route', {
      start, end, hour: state.hour, city: state.city,
    });

    if (res.success) {
      const safest = res.routes.safest;
      const fastest = res.routes.fastest;
      drawRoutes(safest, fastest);
      renderRouteResults(safest, fastest, res.ai_safety_briefing);
      toast('Route calculated!', 'success');
    } else {
      toast(res.error || 'Route planning failed', 'error');
    }
  } catch (e) {
    toast('Network error calculating route', 'error');
  }
  hideLoading();
}

function renderRouteResults(safest, fastest, briefing) {
  const score = safest.safety_avg || 70;
  const extra = (safest.duration_min || 0) - (fastest.duration_min || 0);
  const dangers = (safest.danger_zones || []).length;

  $('#routeResults').innerHTML = `
    <div style="animation:fadeInUp 0.4s ease">
      <h3 class="card-title">Route Metrics</h3>
      <div class="metrics-row" style="grid-template-columns:repeat(2,1fr);margin-bottom:20px">
        <div class="metric-card"><div class="metric-value">${score} / 100</div><div class="metric-label">Safety Score</div></div>
        <div class="metric-card"><div class="metric-value">${safest.duration_min} mins</div><div class="metric-label">Walk Time</div></div>
        <div class="metric-card"><div class="metric-value">${dangers}</div><div class="metric-label">Danger Zones</div></div>
        <div class="metric-card"><div class="metric-value">${extra >= 0 ? '+' : ''}${extra} mins</div><div class="metric-label">Extra Time</div></div>
      </div>
      <h3 class="card-title">AI Route Safety Briefing</h3>
      <div class="briefing-box">${escapeHtml(briefing || 'No briefing available.').replace(/\n/g, '<br>')}</div>
    </div>
  `;
}

// ── Incident Reporting ────────────────────────────────────────────────
async function submitReport() {
  const text = $('#reportText').value.trim();
  if (!text) { toast('Please describe the incident', 'error'); return; }

  showLoading('Processing report with NLP...');
  try {
    const res = await apiPost('/api/report', { text, city: state.city, country: state.country });
    if (res.success) {
      $('#reportResult').innerHTML = `
        <div class="briefing-box" style="background:var(--emerald-100);border-color:#A7F3D0">
          <strong>Report saved!</strong><br>
          Location: (${res.saved_location.lat.toFixed(4)}, ${res.saved_location.lng.toFixed(4)})<br>
          Type: ${res.nlp_parsed.incident_type} · Severity: ${res.nlp_parsed.severity}
        </div>`;
      $('#reportText').value = '';
      toast('Incident report submitted!', 'success');
    } else {
      toast('Could not process report', 'error');
    }
  } catch (e) {
    toast('Network error submitting report', 'error');
  }
  hideLoading();
}

// ── Live Feed ─────────────────────────────────────────────────────────
async function loadFeed() {
  try {
    const [statsRes, feedRes] = await Promise.all([
      apiGet(`/api/stats?city=${encodeURIComponent(state.city)}`),
      apiGet(`/api/feed?city=${encodeURIComponent(state.city)}`),
    ]);

    const s = statsRes.stats || {};
    $('#metTotal').textContent = s.total ?? '—';
    $('#met24h').textContent = s.last_24h ?? '—';
    $('#metVerified').textContent = s.verified ?? '—';
    $('#metSeverity').textContent = (s.avg_severity ?? 0).toFixed(1) + ' / 3';

    const feed = feedRes.feed || [];
    if (feed.length === 0) {
      $('#feedList').innerHTML = `<div class="empty-state"><div class="empty-state-icon">📋</div><p>No reports yet for ${state.city}.</p></div>`;
      return;
    }

    $('#feedList').innerHTML = feed.map((item, i) => {
      const sevClass = item.severity === 3 ? 'sev-3' : item.severity === 2 ? 'sev-2' : 'sev-1';
      const badge = item.verified ? '<span class="badge badge-verified" style="margin-left:8px">Verified</span>' : '';
      const timeAgo = getTimeAgo(item.timestamp);
      const voted = state.votedIds.has(item.id);

      return `
        <div class="feed-card" style="animation-delay:${i * 0.05}s">
          <div style="flex:1">
            <div>
              <span class="feed-type ${sevClass}">${escapeHtml(item.type)}</span>${badge}
              <span style="color:var(--text-muted);font-size:0.78rem;margin-left:8px">${timeAgo}</span>
            </div>
            ${item.description ? `<div class="feed-desc">${escapeHtml(item.description)}</div>` : ''}
            <div class="feed-meta">📍 (${item.lat?.toFixed(4)}, ${item.lng?.toFixed(4)}) · ${item.upvotes} upvotes</div>
          </div>
          <div class="feed-actions">
            ${voted
              ? '<span style="font-size:0.82rem;color:var(--text-muted)">Voted</span>'
              : `<button class="vote-btn" onclick="vote(${item.id},'up')">👍</button>
                 <button class="vote-btn" onclick="vote(${item.id},'down')">👎</button>`
            }
          </div>
        </div>`;
    }).join('');
  } catch (e) {
    toast('Failed to load feed', 'error');
  }
}

async function vote(id, type) {
  try {
    await apiPost('/api/vote', { id, session_id: state.sessionId, vote: type });
    state.votedIds.add(id);
    toast(`Vote recorded`, 'success');
    loadFeed();
  } catch (e) { toast('Vote failed', 'error'); }
}

// ── AI News ───────────────────────────────────────────────────────────
async function fetchNews() {
  showLoading(`Fetching AI news for ${state.city}...`);
  try {
    const res = await apiPost('/api/news', { city: state.city, country: state.country });
    const items = res.raw_news_fetched || [];
    const count = res.ingested_count || 0;
    toast(`Ingested ${count} news alerts for ${state.city}`, 'success');

    $('#newsResults').innerHTML = items.map(item => `
      <div class="briefing-box" style="margin-bottom:8px;padding:12px 16px;font-size:0.85rem">
        <strong>${escapeHtml(item.location_description || state.city)}</strong>
        <span style="color:var(--text-muted);font-size:0.75rem"> (${escapeHtml(item.news_source || 'Alert')})</span><br>
        <span style="color:var(--text-secondary)">${escapeHtml(item.description || '')}</span>
      </div>`).join('');

    loadFeed(); // refresh feed with new data
  } catch (e) {
    toast('Failed to fetch news', 'error');
  }
  hideLoading();
}

// ── City Safety Overview ──────────────────────────────────────────────
async function fetchOverview() {
  showLoading(`Analyzing safety for ${state.city}...`);
  try {
    const res = await apiGet(`/api/overview?city=${encodeURIComponent(state.city)}`);
    $('#overviewResults').innerHTML = `
      <div class="briefing-box" style="font-size:0.88rem">${escapeHtml(res.overview || '')}</div>`;
    toast('Safety overview loaded', 'info');
  } catch (e) { toast('Failed to get overview', 'error'); }
  hideLoading();
}

// ── AI Assistant ──────────────────────────────────────────────────────
async function askAI() {
  const q = $('#aiQuestion').value.trim();
  if (!q) { toast('Please enter a question', 'error'); return; }

  showLoading('Querying AI assistant...');
  try {
    const res = await apiPost('/api/ask', { query: q, city: state.city, country: state.country });
    $('#aiResult').innerHTML = `
      <div class="briefing-box">
        <strong>AI Guidance:</strong><br>${escapeHtml(res.answer || 'No answer available.').replace(/\n/g, '<br>')}
      </div>`;
    toast('AI response received', 'success');
  } catch (e) { toast('AI query failed', 'error'); }
  hideLoading();
}

// ── SOS ───────────────────────────────────────────────────────────────
async function generateSOS() {
  const name = $('#sosName').value.trim();
  const current = $('#sosCurrent').value.trim();
  const dest = $('#sosDest').value.trim();
  if (!name) { toast('Enter your name', 'error'); return; }

  showLoading('Generating SOS...');
  try {
    const res = await apiPost('/api/sos', {
      name, current_location: current, destination: dest, city: state.city,
    });
    $('#sosResult').innerHTML = `
      <div class="briefing-box" style="background:var(--rose-100);border-color:#FECDD3">
        <strong>SMS Alert Text (&lt;160 chars):</strong><br>${escapeHtml(res.message || '')}
      </div>`;
    toast('Emergency SMS generated', 'info');
  } catch (e) { toast('SOS generation failed', 'error'); }
  hideLoading();
}

// ── Tab Switching ─────────────────────────────────────────────────────
function setupTabs() {
  $$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      $$('.tab-panel').forEach(p => p.classList.remove('active'));
      $(`#tab-${btn.dataset.tab}`).classList.add('active');

      // Lazy-load feed data when switching to feed tab
      if (btn.dataset.tab === 'feed') loadFeed();
      // Resize map when switching to route tab
      if (btn.dataset.tab === 'route') setTimeout(() => map?.invalidateSize(), 100);
    });
  });
}

// ── Utilities ─────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getTimeAgo(ts) {
  if (!ts) return 'Recent';
  try {
    const diff = (Date.now() - new Date(ts + ' UTC').getTime()) / 1000;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  } catch { return 'Recent'; }
}

// ── Event Bindings ────────────────────────────────────────────────────
function bindEvents() {
  $('#setCityBtn').addEventListener('click', setCity);
  $('#hourSlider').addEventListener('input', updateHourLabel);
  $('#findRouteBtn').addEventListener('click', findRoute);
  $('#submitReportBtn').addEventListener('click', submitReport);
  $('#fetchNewsBtn').addEventListener('click', fetchNews);
  $('#overviewBtn').addEventListener('click', fetchOverview);
  $('#askAiBtn').addEventListener('click', askAI);
  $('#sosBtn').addEventListener('click', generateSOS);

  // Enter key support
  $('#startInput').addEventListener('keydown', e => { if (e.key === 'Enter') findRoute(); });
  $('#endInput').addEventListener('keydown', e => { if (e.key === 'Enter') findRoute(); });
  $('#aiQuestion').addEventListener('keydown', e => { if (e.key === 'Enter') askAI(); });
}

// ── Init ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  $('#sessionLabel').textContent = `Session: ${state.sessionId}`;
  initMap();
  setupTabs();
  bindEvents();
  updateHourLabel();
  await loadLandmarks();
});
