/**
 * NEXUS-NER | All-in-One Services Test Suite — JavaScript
 * Connects the UI to all backend AI/ML service endpoints and components.
 */

'use strict';

// ── State & Constants ──────────────────────────────────────────────────────

let API_BASE = 'http://localhost:8000';

const RISK_COLORS = {
  SAFE:     '#10b981',
  MODERATE: '#f59e0b',
  HIGH:     '#f97316',
  CRITICAL: '#ef4444',
};

const RISK_EMOJIS = {
  SAFE:     '✅',
  MODERATE: '⚠️',
  HIGH:     '🔶',
  CRITICAL: '🚨',
};

const ACTION_EMOJIS = {
  MONITOR:    '👁',
  WARN:       '⚠️',
  REROUTE:    '↩️',
  BLOCK_ROUTE:'🚫',
  ESCALATE:   '🆘',
};

// ── Helpers ────────────────────────────────────────────────────────────────

function getApiBase() {
  return (document.getElementById('apiBaseInput').value || 'http://localhost:8000').replace(/\/$/, '');
}

function setLoading(show, text = 'Processing AI Pipeline…') {
  const overlay = document.getElementById('loadingOverlay');
  const txtEl = document.getElementById('loadingText');
  if (txtEl) txtEl.textContent = text;
  overlay.classList.toggle('visible', show);
}

function setStatus(state, text) {
  const dot  = document.getElementById('statusDot');
  const span = document.getElementById('statusText');
  if (dot) dot.className = 'status-dot ' + state;
  if (span) span.textContent = text;
}

function fmt(json) {
  return JSON.stringify(json, null, 2);
}

function pct(v) {
  return (v * 100).toFixed(1) + '%';
}

function etaStr(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${String(m).padStart(2, '0')}m`;
}

async function apiFetch(path, method = 'GET', body = null) {
  const base = getApiBase();
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);

  const t0 = performance.now();
  const res = await fetch(base + path, opts);
  const t1 = performance.now();
  const latency = Math.round(t1 - t0);

  const data = await res.json();
  if (!res.ok) throw { status: res.status, data, latency };
  return { data, latency };
}

// ── Range slider sync ──────────────────────────────────────────────────────

window.syncVal = function(input, spanId, isFloat = false) {
  const el = document.getElementById(spanId);
  if (el) el.textContent = isFloat ? parseFloat(input.value).toFixed(2) : input.value;
};

// ── Tab navigation ─────────────────────────────────────────────────────────

const TAB_TITLES = {
  health:    'System Health & Status',
  features:  'Feature Transformer Explorer',
  predict:   'Disruption Risk Predictor & Explainability',
  risk:      'Multi-Signal Risk Scoring Engine',
  routes:    'Route Intelligence & Graph Evaluator',
  recommend: 'Operational Decision & Action Engine',
  scenarios: 'What-If Simulation Scenario Lab',
  metrics:   'Model Evaluation & Metrics',
  suite:     'In-Browser Automated Test Suite',
};

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const tab = el.dataset.tab;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    const target = document.getElementById('tab-' + tab);
    if (target) target.classList.add('active');
    document.getElementById('pageTitle').textContent = TAB_TITLES[tab] || tab;

    if (tab === 'features') calcFeatures();
  });
});

// ── TAB 1: System Health ───────────────────────────────────────────────────

async function runHealthCheck() {
  setLoading(true, 'Pinging Service Endpoint…');
  setStatus('loading', 'Checking…');
  try {
    const { data, latency } = await apiFetch('/ai/health');
    document.getElementById('healthOutput').textContent = fmt(data);

    const isOk = data.status === 'ok';
    document.getElementById('hStatus').textContent   = data.status?.toUpperCase() || 'OK';
    document.getElementById('hStatus').className     = 'stat-value ' + (isOk ? 'ok' : 'error');
    document.getElementById('hModel').textContent    = data.model_loaded ? 'LOADED' : 'NOT FOUND';
    document.getElementById('hModel').className      = 'stat-value ' + (data.model_loaded ? 'ok' : 'error');
    document.getElementById('hModelType').textContent = data.model_type || '—';
    document.getElementById('hLatency').textContent  = `${latency} ms`;

    setStatus(isOk ? 'ok' : 'error', isOk ? 'Online' : 'Degraded');
    document.getElementById('apiUrlLabel').textContent = getApiBase().replace(/https?:\/\//, '');
    document.getElementById('apiLatency').textContent = `${latency}ms`;
  } catch (err) {
    document.getElementById('healthOutput').textContent = fmt(err.data || String(err));
    document.getElementById('hStatus').textContent = 'OFFLINE';
    document.getElementById('hStatus').className = 'stat-value error';
    document.getElementById('hModel').textContent = 'OFFLINE';
    document.getElementById('hLatency').textContent = 'Timeout';
    setStatus('error', 'Offline');
  } finally {
    setLoading(false);
  }
}

document.getElementById('btnHealth')?.addEventListener('click', runHealthCheck);
document.getElementById('refreshBtn')?.addEventListener('click', runHealthCheck);

// ── TAB 2: Feature Transformer ─────────────────────────────────────────────

window.calcFeatures = function() {
  const r1h = parseFloat(document.getElementById('f_r1h')?.value || 75);
  const r3h = parseFloat(document.getElementById('f_r3h')?.value || 180);
  const r6h = parseFloat(document.getElementById('f_r6h')?.value || 260);
  const r24h = parseFloat(document.getElementById('f_r24h')?.value || 380);
  const rc  = parseFloat(document.getElementById('f_rc')?.value || 0.35);
  const ms  = parseFloat(document.getElementById('f_ms')?.value || 0.40);
  const tl  = parseFloat(document.getElementById('f_tl')?.value || 0.70);
  const spd = parseFloat(document.getElementById('f_spd')?.value || 28);
  const sl  = parseFloat(document.getElementById('f_sl')?.value || 22);
  const rd  = parseFloat(document.getElementById('f_rd')?.value || 0.8);
  const hi  = parseFloat(document.getElementById('f_hi')?.value || 6);

  // Exact formulas from services/ai/features/feature_engineering.py
  const rainfall_intensity = r1h / (r24h + 1.0);
  const rainfall_accumulation = (r1h * 0.5) + (r3h * 0.3) + (r6h * 0.2);
  const rainfall_change = (r1h * 3.0) - r3h;
  const slope_norm = Math.min(sl / 45.0, 1.0);
  const river_prox = Math.max(0.0, 1.0 - (rd / 10.0));
  const terrain_risk = (slope_norm * 0.6) + (river_prox * 0.4);
  const speed_score = 1.0 - Math.min(spd / 60.0, 1.0);
  const congestion_score = (tl * 0.6) + (speed_score * 0.4);
  const road_condition_score = (rc * 0.6) + (ms * 0.4);
  const historical_risk = Math.min((hi / 10.0) * 0.7 + (hi * 0.3) / 5.0, 1.0);

  const container = document.getElementById('featureCalcResults');
  if (!container) return;

  const features = [
    { name: 'rainfall_intensity', val: rainfall_intensity.toFixed(4), desc: 'r1h / (r24h + 1.0)' },
    { name: 'rainfall_accumulation', val: rainfall_accumulation.toFixed(1) + ' mm', desc: '0.5·r1h + 0.3·r3h + 0.2·r6h' },
    { name: 'rainfall_change', val: rainfall_change.toFixed(1) + ' mm', desc: '3·r1h - r3h' },
    { name: 'terrain_risk', val: (terrain_risk * 100).toFixed(1) + '%', desc: '0.6·slope_norm + 0.4·river_prox' },
    { name: 'congestion_score', val: (congestion_score * 100).toFixed(1) + '%', desc: '0.6·traffic + 0.4·speed_loss' },
    { name: 'road_condition_score', val: (road_condition_score * 100).toFixed(1) + '%', desc: '0.6·condition + 0.4·maint' },
    { name: 'historical_risk', val: (historical_risk * 100).toFixed(1) + '%', desc: 'Weighted incident history' },
    { name: 'total_feature_vector', val: '25 dimensions', desc: 'Scaled via StandardScaler' },
  ];

  container.innerHTML = features.map(f => `
    <div class="calc-card">
      <div class="calc-card-title">${f.name}</div>
      <div class="calc-card-val">${f.val}</div>
      <div class="calc-card-formula">${f.desc}</div>
    </div>
  `).join('');
};

document.getElementById('btnFeatureDefaults')?.addEventListener('click', () => {
  document.getElementById('f_r1h').value = 75;
  document.getElementById('f_r3h').value = 180;
  document.getElementById('f_r6h').value = 260;
  document.getElementById('f_r24h').value = 380;
  document.getElementById('f_rc').value = 0.35;
  document.getElementById('f_ms').value = 0.40;
  document.getElementById('f_tl').value = 0.70;
  document.getElementById('f_spd').value = 28;
  document.getElementById('f_sl').value = 22;
  document.getElementById('f_rd').value = 0.8;
  document.getElementById('f_hi').value = 6;
  calcFeatures();
});

// ── TAB 3: Predict & Explain ───────────────────────────────────────────────

const DEMO_PREDICT = {
  road_id: 'NH13_042',
  rainfall_1h: 90, rainfall_3h: 210,
  traffic_level: 0.75, road_condition: 0.30,
  slope: 18.0, river_distance: 0.9, historical_incidents: 7,
};

function loadDemoPredict() {
  document.getElementById('p_road_id').value = DEMO_PREDICT.road_id;
  setSlider('p_rainfall_1h',          DEMO_PREDICT.rainfall_1h,          'p_rainfall_1h_v');
  setSlider('p_rainfall_3h',          DEMO_PREDICT.rainfall_3h,          'p_rainfall_3h_v');
  setSlider('p_traffic_level',        DEMO_PREDICT.traffic_level,        'p_traffic_v', true);
  setSlider('p_road_condition',       DEMO_PREDICT.road_condition,       'p_road_v', true);
  setSlider('p_slope',                DEMO_PREDICT.slope,                'p_slope_v');
  setSlider('p_river_distance',       DEMO_PREDICT.river_distance,       'p_river_v', true);
  setSlider('p_historical_incidents', DEMO_PREDICT.historical_incidents,  'p_hist_v');
}

function setSlider(id, val, labelId, isFloat = false) {
  const el = document.getElementById(id);
  if (el) { el.value = val; syncVal(el, labelId, isFloat); }
}

document.getElementById('btnLoadDemo')?.addEventListener('click', loadDemoPredict);

document.getElementById('predictForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  setLoading(true, 'Running Disruption Predictor…');

  const body = {
    road_id: document.getElementById('p_road_id').value,
    features: {
      rainfall_1h:          parseFloat(document.getElementById('p_rainfall_1h').value),
      rainfall_3h:          parseFloat(document.getElementById('p_rainfall_3h').value),
      traffic_level:        parseFloat(document.getElementById('p_traffic_level').value),
      road_condition:       parseFloat(document.getElementById('p_road_condition').value),
      slope:                parseFloat(document.getElementById('p_slope').value),
      river_distance:       parseFloat(document.getElementById('p_river_distance').value),
      historical_incidents: parseInt(document.getElementById('p_historical_incidents').value),
    },
  };

  try {
    const { data } = await apiFetch('/ai/predict-risk', 'POST', body);
    document.getElementById('predictOutput').textContent = fmt(data);
    renderPredictResult(data);
  } catch (err) {
    document.getElementById('predictOutput').textContent = fmt(err.data || String(err));
    document.getElementById('riskResultContent').innerHTML =
      `<div class="empty-state" style="color:var(--critical)">Error: ${err.data?.detail || err}</div>`;
  } finally {
    setLoading(false);
  }
});

function renderPredictResult(data) {
  const level = data.risk_level;
  const color = RISK_COLORS[level] || '#fff';
  const probPct = (data.probability * 100).toFixed(1);
  const finalPct = (data.final_risk * 100).toFixed(1);
  const emoji = RISK_EMOJIS[level] || '';

  document.getElementById('riskResultContent').innerHTML = `
    <div class="risk-gauge">
      <div class="risk-probability" style="-webkit-text-fill-color:${color}">${probPct}%</div>
      <div class="risk-label-badge ${level}">${emoji} ${level}</div>
      <div class="risk-bar-track" style="width:100%;margin-bottom:8px">
        <div class="risk-bar-fill ${level}" style="width:${probPct}%"></div>
      </div>
      <div style="font-size:11.5px;color:var(--text-muted)">
        ML Probability — Multi-Signal Risk Score: <strong style="color:${color}">${finalPct}%</strong>
      </div>
    </div>`;

  const comps = data.components || {};
  const compKeys = Object.keys(comps);
  if (compKeys.length) {
    document.getElementById('riskComponents').innerHTML = `
      <div class="components-list">
        ${compKeys.map(k => `
          <div class="component-row">
            <div class="component-header">
              <span>${k.replace(/_/g, ' ')}</span>
              <span style="color:var(--cyan)">${(comps[k] * 100).toFixed(1)}%</span>
            </div>
            <div class="component-bar-track">
              <div class="component-bar-fill" style="width:${(comps[k]*100).toFixed(1)}%"></div>
            </div>
          </div>`).join('')}
      </div>`;
  }

  const factors = data.factors || [];
  document.getElementById('riskFactors').innerHTML = factors.length
    ? factors.map(f => `<li>${f}</li>`).join('')
    : '<li class="empty-state">No significant risk factors identified.</li>';
}

// ── TAB 5: Route Intelligence ──────────────────────────────────────────────

document.getElementById('routeForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  setLoading(true, 'Evaluating Route Alternatives…');

  const body = {
    origin:      document.getElementById('r_origin').value,
    destination: document.getElementById('r_destination').value,
    cargo_type:  document.getElementById('r_cargo_type').value,
    priority:    document.getElementById('r_priority').value,
  };

  try {
    const { data } = await apiFetch('/ai/route-intelligence', 'POST', body);
    document.getElementById('routeOutput').textContent = fmt(data);
    renderRouteResults(data);
  } catch (err) {
    document.getElementById('routeOutput').textContent = fmt(err.data || String(err));
    document.getElementById('routeResults').innerHTML =
      `<div class="empty-state" style="color:var(--critical)">Error: ${err.data?.detail || err}</div>`;
  } finally {
    setLoading(false);
  }
});

function renderRouteResults(data) {
  const routes    = data.all_routes || [];
  const fastestId  = data.fastest?.route_id;
  const safestId   = data.safest?.route_id;
  const balancedId = data.balanced?.route_id;
  const recId      = data.recommended?.route_id;

  document.getElementById('routeResults').innerHTML = routes.length
    ? `<div class="route-cards">
        ${routes.map(r => {
          const isRec = r.route_id === recId;
          const isFst = r.route_id === fastestId;
          const isSft = r.route_id === safestId;
          const isBal = r.route_id === balancedId;
          const color = RISK_COLORS[r.risk_level];
          const badges = [
            isFst ? '<span class="route-badge fastest">⚡ Fastest</span>' : '',
            isSft ? '<span class="route-badge safest">🛡 Safest</span>'   : '',
            isBal && !isFst && !isSft ? '<span class="route-badge balanced">⚖ Balanced</span>' : '',
            isRec ? '<span class="route-badge recommended">✅ Recommended</span>' : '',
          ].filter(Boolean).join(' ');

          return `<div class="route-card ${isRec ? 'recommended' : ''}">
            <div class="route-info">
              <div class="route-label">${r.label || r.route_id}</div>
              <div class="route-desc">${r.description || ''}</div>
              <div style="margin-top:6px">${badges}</div>
            </div>
            <div class="route-stats">
              <div>
                <div class="route-stat-val">${etaStr(r.eta_minutes)}</div>
                <div class="route-stat-lbl">ETA</div>
              </div>
              <div>
                <div class="route-stat-val" style="color:${color}">${pct(r.risk)}</div>
                <div class="route-stat-lbl" style="color:${color}">${r.risk_level}</div>
              </div>
            </div>
          </div>`;
        }).join('')}
      </div>`
    : '<div class="empty-state">No routes returned.</div>';

  const rec = data.recommended;
  if (rec) {
    document.getElementById('recommendationCard').style.display = 'block';
    document.getElementById('routeRecommendation').innerHTML =
      `<strong>Route ${rec.route_id?.toUpperCase()}</strong> — ${rec.reason}`;
  }
}

// ── TAB 6: Decision Engine ─────────────────────────────────────────────────

const DEMO_REC = {
  road_id: 'NH13_042',
  rainfall_1h: 90, rainfall_3h: 210,
  road_condition: 0.30, traffic_level: 0.75,
  slope: 18, river_distance: 0.9, historical_incidents: 7,
  cargo_type: 'medical', priority: 'emergency',
};

function loadDemoRec() {
  document.getElementById('rec_road_id').value = DEMO_REC.road_id;
  setSlider('rec_r1h', DEMO_REC.rainfall_1h,    'rec_r1h_v');
  setSlider('rec_r3h', DEMO_REC.rainfall_3h,    'rec_r3h_v');
  setSlider('rec_rc',  DEMO_REC.road_condition,  'rec_rc_v', true);
  setSlider('rec_tl',  DEMO_REC.traffic_level,   'rec_tl_v', true);
  setSlider('rec_sl',  DEMO_REC.slope,           'rec_sl_v');
  setSlider('rec_rd',  DEMO_REC.river_distance,  'rec_rd_v', true);
  setSlider('rec_hi',  DEMO_REC.historical_incidents, 'rec_hi_v');
  document.getElementById('rec_cargo').value    = DEMO_REC.cargo_type;
  document.getElementById('rec_priority').value = DEMO_REC.priority;
}

document.getElementById('btnLoadDemoRec')?.addEventListener('click', loadDemoRec);

document.getElementById('recommendForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  setLoading(true, 'Executing Recommendation Classifier…');

  const body = {
    road_id: document.getElementById('rec_road_id').value,
    features: {
      rainfall_1h:          parseFloat(document.getElementById('rec_r1h').value),
      rainfall_3h:          parseFloat(document.getElementById('rec_r3h').value),
      road_condition:       parseFloat(document.getElementById('rec_rc').value),
      traffic_level:        parseFloat(document.getElementById('rec_tl').value),
      slope:                parseFloat(document.getElementById('rec_sl').value),
      river_distance:       parseFloat(document.getElementById('rec_rd').value),
      historical_incidents: parseInt(document.getElementById('rec_hi').value),
    },
    cargo_type: document.getElementById('rec_cargo').value,
    priority:   document.getElementById('rec_priority').value,
  };

  try {
    const { data } = await apiFetch('/ai/recommend-action', 'POST', body);
    document.getElementById('recommendOutput').textContent = fmt(data);
    renderActionResult(data);
  } catch (err) {
    document.getElementById('recommendOutput').textContent = fmt(err.data || String(err));
    document.getElementById('actionResult').innerHTML =
      `<div class="empty-state" style="color:var(--critical)">Error: ${err.data?.detail || err}</div>`;
  } finally {
    setLoading(false);
  }
});

function renderActionResult(data) {
  const action  = data.action;
  const emoji   = ACTION_EMOJIS[action] || '●';
  const factors = data.factors || [];

  const card = document.getElementById('actionCard');
  card.className = `card action-result-card ${action}`;

  document.getElementById('actionResult').innerHTML = `
    <div class="action-display">
      <div class="action-badge ${action}">${emoji} ${action.replace('_', ' ')}</div>
      <div class="action-priority">Priority: <strong>${data.priority}</strong> &nbsp;·&nbsp; Risk: <strong>${pct(data.risk_score)}</strong> (${data.risk_level}) &nbsp;·&nbsp; Mode: <strong>${data.thresholds_applied}</strong></div>
      <div class="action-reason">${data.reason}</div>
      ${factors.length ? `
        <div class="action-factors">
          <div class="action-factors-title">Contributing Factors</div>
          ${factors.map(f => `<span class="factor-tag">${f}</span>`).join('')}
        </div>` : ''}
    </div>`;
}

// ── TAB 7: Scenario Lab ────────────────────────────────────────────────────

async function runScenarios() {
  setLoading(true, 'Running 7 Simulation Scenarios…');
  const roadId = document.getElementById('scenarioRoadId')?.value || 'NH13_042';
  try {
    const { data } = await apiFetch(`/ai/scenarios?road_id=${encodeURIComponent(roadId)}`);
    document.getElementById('scenariosOutput').textContent = fmt(data);
    renderScenarios(data.scenarios || []);
  } catch (err) {
    document.getElementById('scenariosOutput').textContent = fmt(err.data || String(err));
    document.getElementById('scenariosGrid').innerHTML = `<div class="empty-state" style="color:var(--critical)">Error: ${err.data?.detail || err}</div>`;
  } finally {
    setLoading(false);
  }
}

function renderScenarios(scenarios) {
  const grid = document.getElementById('scenariosGrid');
  if (!scenarios.length) { grid.innerHTML = '<div class="empty-state">No scenarios returned.</div>'; return; }

  grid.innerHTML = scenarios.map(s => {
    const level = s.risk_level;
    const color = RISK_COLORS[level] || '#fff';
    const pctVal = (s.final_risk * 100).toFixed(0);
    const emoji = RISK_EMOJIS[level] || '';

    return `
      <div class="scenario-card">
        <div class="scenario-name" style="color:${color}">${emoji} ${s.scenario.replace(/_/g, ' ')}</div>
        <div class="scenario-description">${s.description}</div>
        <div class="scenario-probability" style="color:${color}">${pctVal}%</div>
        <div class="scenario-level" style="color:${color}">${level}</div>
        <div class="scenario-bar-track">
          <div class="scenario-bar-fill" style="width:${pctVal}%;background:${color}"></div>
        </div>
        <div class="scenario-inputs">
          <span class="scenario-chip">Rain: ${s.inputs.rainfall_1h}mm/h</span>
          <span class="scenario-chip">Road: ${s.inputs.road_condition?.toFixed(2)}</span>
          <span class="scenario-chip">Traffic: ${(s.inputs.traffic_level * 100).toFixed(0)}%</span>
        </div>
      </div>`;
  }).join('');
}

document.getElementById('btnScenarios')?.addEventListener('click', runScenarios);

// ── TAB 9: Automated Test Suite ────────────────────────────────────────────

async function runTestSuite() {
  const tests = [
    {
      row: 'test-row-1',
      path: '/ai/health',
      method: 'GET',
      check: d => d.status === 'ok' && d.model_loaded === true,
    },
    {
      row: 'test-row-2',
      path: '/ai/scenarios?road_id=NH13_042',
      method: 'GET',
      check: d => Array.isArray(d.scenarios) && d.scenarios.length >= 5,
    },
    {
      row: 'test-row-3',
      path: '/ai/predict-risk',
      method: 'POST',
      body: {
        road_id: 'NH13_042',
        features: { rainfall_1h: 60, rainfall_3h: 140, traffic_level: 0.5, road_condition: 0.6, slope: 12, river_distance: 2.0, historical_incidents: 3 },
      },
      check: d => typeof d.probability === 'number' && d.probability >= 0 && d.probability <= 1,
    },
    {
      row: 'test-row-4',
      path: '/ai/route-intelligence',
      method: 'POST',
      body: { origin: 'Guwahati', destination: 'Tawang', cargo_type: 'medical', priority: 'emergency' },
      check: d => d.fastest && d.safest && d.recommended,
    },
    {
      row: 'test-row-5',
      path: '/ai/recommend-action',
      method: 'POST',
      body: {
        road_id: 'NH13_042',
        features: { rainfall_1h: 90, rainfall_3h: 210, traffic_level: 0.8, road_condition: 0.2, slope: 25, river_distance: 0.5, historical_incidents: 8 },
        cargo_type: 'medical', priority: 'emergency',
      },
      check: d => ['REROUTE', 'BLOCK_ROUTE', 'ESCALATE'].includes(d.action),
    },
  ];

  for (const t of tests) {
    const rowEl = document.getElementById(t.row);
    if (!rowEl) continue;
    const timeEl = rowEl.querySelector('.suite-time');
    const statusEl = rowEl.querySelector('.suite-status');

    statusEl.innerHTML = '<span class="badge-pill running">RUNNING…</span>';

    try {
      const { data, latency } = await apiFetch(t.path, t.method, t.body);
      const passed = t.check(data);
      timeEl.textContent = `${latency} ms`;
      statusEl.innerHTML = passed
        ? '<span class="badge-pill pass">✅ PASS</span>'
        : '<span class="badge-pill fail">❌ FAIL</span>';
    } catch (err) {
      timeEl.textContent = `${err.latency || 0} ms`;
      statusEl.innerHTML = '<span class="badge-pill fail">❌ ERR</span>';
    }
  }
}

document.getElementById('btnRunSuite')?.addEventListener('click', runTestSuite);

// ── Initialization ─────────────────────────────────────────────────────────

(async function init() {
  calcFeatures();
  try {
    setStatus('loading', 'Connecting…');
    await runHealthCheck();
  } catch (_) {
    setStatus('error', 'Offline');
  }
})();
