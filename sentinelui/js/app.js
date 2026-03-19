/**
 * SentinelTwin AI — Main Application Controller
 * Orchestrates all dashboard panels, WebSocket data flow,
 * chart updates, and 3D digital twin interaction.
 */

// ─── Global state ───────────────────────────────────────────────────────────
const APP = {
  factoryState: null,
  alerts: [],
  incidents: [],
  predictions: {},
  anomalies: [],
  cyberThreats: [],
  healingActions: [],
  efficiency: null,
  lifecycle: {},
  activeScenarios: [],
  wsConnected: false,
  charts: null,
  twin: null,
  activeView: 'overview',
  defects: [],
  optimizationRecs: [],
  rootCauses: {},
};

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? `http://${window.location.hostname}:8000`
  : '';
const WS_URL = `ws://${window.location.hostname}:${window.location.hostname === 'localhost' ? '8000' : window.location.port || '8000'}/ws`;

// ─── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  APP.charts = new ChartManager();
  initCharts();
  initNavigation();
  initScenarioButtons();
  initTwin();
  connectWebSocket();
  startClock();
  loadInitialData();
});

// ─── WebSocket ───────────────────────────────────────────────────────────────
function connectWebSocket() {
  new SentinelWebSocket(WS_URL,
    (msg) => handleWSMessage(msg),
    (connected) => {
      APP.wsConnected = connected;
      const dot = document.getElementById('conn-dot');
      const label = document.getElementById('conn-label');
      if (dot) dot.className = 'conn-dot' + (connected ? '' : ' disconnected');
      if (label) label.textContent = connected ? 'Live' : 'Reconnecting…';
    }
  );
}

function handleWSMessage(msg) {
  const { type, data } = msg;
  switch (type) {
    case 'sensor_update':       handleSensorUpdate(data); break;
    case 'alert':               handleAlert(data); break;
    case 'anomaly_detected':    handleAnomaly(data); break;
    case 'predictive_maintenance': handlePrediction(data); break;
    case 'cyber_threat':        handleCyberThreat(data); break;
    case 'cyber_response':      handleCyberResponse(data); break;
    case 'self_healing_action': handleHealingAction(data); break;
    case 'defect_detected':     handleDefect(data); break;
    case 'incident_timeline':   handleIncidents(data); break;
    case 'efficiency_score':    handleEfficiency(data); break;
    case 'root_cause_analysis': handleRCA(data); break;
    case 'production_optimization': handleOptimization(data); break;
    case 'scenario_update':     handleScenarioUpdate(data); break;
  }
}

// ─── Sensor Update ───────────────────────────────────────────────────────────
function handleSensorUpdate(data) {
  APP.factoryState = data;
  if (data.efficiency) APP.efficiency = data.efficiency;
  if (data.lifecycle) APP.lifecycle = data.lifecycle;
  if (data.active_scenarios) APP.activeScenarios = data.active_scenarios;

  updateMachineCards(data.machines);
  updateKPIs(data);
  updateChartData(data);
  if (APP.twin) APP.twin.updateMachineStates(data.machines);
  updateFactoryStatus(data.factory);
}

function updateMachineCards(machines) {
  if (!machines) return;
  Object.entries(machines).forEach(([id, data]) => {
    const card = document.getElementById(`machine-card-${id}`);
    if (!card) return;
    const sensors = data.sensors || {};
    const status = data.status || 'normal';
    const health = data.health_score || 100;

    card.className = `machine-card status-${status}`;

    const tempEl = card.querySelector('.sensor-temp');
    const vibEl = card.querySelector('.sensor-vib');
    const currEl = card.querySelector('.sensor-curr');
    const healthFill = card.querySelector('.machine-health-fill');
    const actionTag = card.querySelector('.need-action-tag');

    if (tempEl) {
      tempEl.textContent = (sensors.temperature || 0).toFixed(1) + '°C';
      tempEl.className = 'sensor-mini-val ' + getSensorClass(sensors.temperature, 75, 90);
    }
    if (vibEl) {
      vibEl.textContent = (sensors.vibration || 0).toFixed(2);
      vibEl.className = 'sensor-mini-val ' + getSensorClass(sensors.vibration, 7, 10);
    }
    if (currEl) {
      currEl.textContent = (sensors.motor_current || 0).toFixed(1) + 'A';
      currEl.className = 'sensor-mini-val ' + getSensorClass(sensors.motor_current, 80, 95);
    }
    if (healthFill) {
      healthFill.style.width = health + '%';
      healthFill.style.background = health >= 70 ? 'var(--success)' : health >= 40 ? 'var(--warning)' : 'var(--danger)';
    }
    if (actionTag) {
      actionTag.style.display = (status === 'failure' || status === 'critical') ? 'inline-block' : 'none';
    }
  });
}

function updateKPIs(data) {
  const eff = data.efficiency || APP.efficiency;
  if (eff) {
    setEl('kpi-efficiency', eff.factory_efficiency_score?.toFixed(1) + '%');
    setEl('kpi-utilization', eff.raw_metrics?.avg_utilization_pct?.toFixed(1) + '%');
    setEl('kpi-throughput', eff.raw_metrics?.current_throughput?.toFixed(1) + '%');
    setEl('kpi-health', eff.raw_metrics?.avg_health_score?.toFixed(1) + '%');
    setEl('sidebar-eff', eff.factory_efficiency_score?.toFixed(1) + '%');
    setEl('failure-risk-label', eff.raw_metrics?.failure_risk);
  }
  const factory = data.factory || {};
  setEl('kpi-production', Math.round(factory.total_production_units || 0).toLocaleString());
  if (factory.bottleneck_machine) {
    setEl('kpi-bottleneck', factory.bottleneck_machine);
    setElStyle('bottleneck-row', 'display', 'flex');
  } else {
    setElStyle('bottleneck-row', 'display', 'none');
  }
}

function updateChartData(data) {
  const machines = data.machines || {};
  const factory = data.factory || {};

  // Production throughput chart
  APP.charts.pushData('chart-production', factory.current_throughput || 85);

  // Machine health chart (all 5 machines)
  ['M1','M2','M3','M4','M5'].forEach((id, idx) => {
    const health = machines[id]?.health_score || 100;
    APP.charts.pushData('chart-machine-health', health, idx);
  });

  // Bar chart: utilization
  const utils = ['M1','M2','M3','M4','M5'].map(id => machines[id]?.sensors?.load || 70);
  APP.charts.updateBarData('chart-utilization', utils);

  // Radar
  if (APP.efficiency) {
    const comp = APP.efficiency.components || {};
    APP.charts.updateRadar('chart-radar', [
      comp.machine_utilization || 85,
      comp.production_throughput || 88,
      comp.downtime_score || 92,
      comp.energy_efficiency || 87,
      comp.failure_risk_score || 90,
    ]);
  }

  // Sensor charts for selected machine
  const m1 = machines['M1'];
  if (m1) {
    APP.charts.pushData('chart-temp-m1', m1.sensors?.temperature || 0);
    APP.charts.pushData('chart-vib-m1', m1.sensors?.vibration || 0);
  }
}

// ─── Alert Handler ────────────────────────────────────────────────────────────
function handleAlert(data) {
  APP.alerts.unshift(data);
  if (APP.alerts.length > 100) APP.alerts.pop();
  renderAlerts();
  updateAlertBadge();
}

function renderAlerts() {
  const list = document.getElementById('alert-list');
  if (!list) return;
  const recent = APP.alerts.slice(0, 15);
  list.innerHTML = recent.map(a => `
    <div class="alert-item ${a.level || 'low'} fade-in">
      <div class="alert-level-dot ${a.level || 'low'}"></div>
      <div class="alert-content">
        <div class="alert-title">${escHtml(a.title || 'Alert')}</div>
        <div class="alert-desc">${escHtml(a.description || '')}</div>
      </div>
      <div class="alert-time">${formatTime(a.timestamp)}</div>
    </div>
  `).join('');
}

function updateAlertBadge() {
  const badge = document.getElementById('alert-count-badge');
  if (badge) {
    const critical = APP.alerts.filter(a => a.level === 'critical').length;
    badge.textContent = critical > 0 ? critical : APP.alerts.length;
    badge.className = 'panel-badge ' + (critical > 0 ? 'danger' : 'warning');
  }
}

// ─── Anomaly Handler ─────────────────────────────────────────────────────────
function handleAnomaly(data) {
  APP.anomalies.unshift(data);
  if (APP.anomalies.length > 50) APP.anomalies.pop();
  renderAnomalies();
}

function renderAnomalies() {
  const container = document.getElementById('anomaly-list');
  if (!container) return;
  const items = APP.anomalies.slice(0, 8);
  container.innerHTML = items.map(a => `
    <div class="alert-item ${a.severity || 'medium'} fade-in">
      <div class="alert-level-dot ${a.severity || 'medium'}"></div>
      <div class="alert-content">
        <div class="alert-title">${a.machine_name || a.machine_id}: ${(a.anomaly_type||'').replace(/_/g,' ')}</div>
        <div class="alert-desc">Score: ${(a.composite_score||0).toFixed(3)} | Votes: ${a.detector_votes||0}/3 detectors</div>
      </div>
      <div class="alert-time">${formatTime(a.timestamp)}</div>
    </div>
  `).join('') || '<div class="text-muted" style="padding:12px;font-size:12px">No anomalies detected</div>';
}

// ─── Predictive Maintenance ───────────────────────────────────────────────────
function handlePrediction(data) {
  APP.predictions[data.machine_id] = data;
  renderPredictions();
}

function renderPredictions() {
  const container = document.getElementById('prediction-list');
  if (!container) return;
  const preds = Object.values(APP.predictions).sort((a, b) => b.failure_probability - a.failure_probability);
  container.innerHTML = preds.map(p => {
    const prob = p.failure_probability_pct || (p.failure_probability * 100);
    const level = prob >= 85 ? 'critical' : prob >= 65 ? 'high' : prob >= 40 ? 'medium' : 'low';
    const explanation = p.explanation?.feature_ranking || p.contributing_sensors || [];
    return `
      <div class="panel-body" style="border-bottom:1px solid var(--border);padding-bottom:12px">
        <div class="flex-between" style="margin-bottom:4px">
          <span style="font-weight:600;font-size:13px">${p.machine_name||p.machine_id}</span>
          <span class="panel-badge ${level}">${prob.toFixed(1)}%</span>
        </div>
        <div class="prediction-bar">
          <div class="prediction-fill ${level}" style="width:${Math.min(100,prob)}%"></div>
        </div>
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">
          RUL: <strong>${(p.rul_hours||0).toFixed(0)}h</strong> (${(p.rul_days||0).toFixed(1)} days) | ${p.alert_level||''}
        </div>
        ${explanation.length ? `
        <div class="explanation-tag">
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);margin-bottom:3px;text-transform:uppercase">Contributing Factors</div>
          ${explanation.slice(0,3).map(f => `
            <div class="explanation-factor">
              <span>${f.label||f.factor||f.sensor}</span>
              <span>+${(f.contribution_pct||0).toFixed(0)}%</span>
            </div>
          `).join('')}
        </div>` : ''}
        <div style="font-size:11px;color:var(--text-secondary);margin-top:4px">${escHtml(p.recommendation||'')}</div>
      </div>
    `;
  }).join('') || '<div class="panel-body text-muted" style="font-size:12px">No active predictions</div>';
}

// ─── Cybersecurity ────────────────────────────────────────────────────────────
function handleCyberThreat(data) {
  APP.cyberThreats.unshift(data);
  if (APP.cyberThreats.length > 30) APP.cyberThreats.pop();
  renderCyberThreats();
}

function handleCyberResponse(data) {
  renderCyberResponse(data);
}

function renderCyberThreats() {
  const container = document.getElementById('cyber-threat-list');
  if (!container) return;
  container.innerHTML = APP.cyberThreats.slice(0, 6).map(t => `
    <div class="cyber-threat-card fade-in">
      <div class="cyber-threat-header">🛡️ ${(t.threat_type||'Unknown Threat').replace(/_/g,' ').toUpperCase()}</div>
      <div class="cyber-threat-desc">
        Target: <strong>${t.target_machine||'Network'}</strong> | Severity: <strong>${t.severity||'critical'}</strong>
        ${t.description ? '<br>' + escHtml(t.description) : ''}
      </div>
      <span style="font-size:10px;color:var(--text-muted)">${formatTime(t.timestamp)}</span>
    </div>
  `).join('') || '<div style="padding:12px;font-size:12px;color:var(--text-muted)">No active threats</div>';
  const badge = document.getElementById('cyber-badge');
  if (badge) {
    const recent = APP.cyberThreats.filter(t => {
      const age = (Date.now() - new Date(t.timestamp).getTime()) / 1000;
      return age < 60;
    }).length;
    badge.textContent = recent > 0 ? `${recent} ACTIVE` : 'Secure';
    badge.className = 'panel-badge ' + (recent > 0 ? 'danger' : 'success');
  }
}

function renderCyberResponse(response) {
  const container = document.getElementById('cyber-response-list');
  if (!container) return;
  const existing = container.innerHTML;
  const newItem = `
    <div class="healing-action-card fade-in">
      <div class="healing-icon">🔒</div>
      <div class="healing-content">
        <div class="healing-title">${(response.action||'Auto Response').replace(/_/g,' ').toUpperCase()}</div>
        <div class="healing-desc">${escHtml(response.description||response.response_description||'Automated defense response activated')}</div>
        <span style="font-size:10px;color:var(--text-muted)">${formatTime(response.timestamp)}</span>
      </div>
    </div>
  `;
  container.innerHTML = newItem + existing;
}

// ─── Self-Healing ─────────────────────────────────────────────────────────────
function handleHealingAction(data) {
  APP.healingActions.unshift(data);
  if (APP.healingActions.length > 20) APP.healingActions.pop();
  renderHealingActions();
}

function renderHealingActions() {
  const container = document.getElementById('healing-list');
  if (!container) return;
  container.innerHTML = APP.healingActions.slice(0, 6).map(h => `
    <div class="healing-action-card fade-in">
      <div class="healing-icon">♻️</div>
      <div class="healing-content">
        <div class="healing-title">${(h.action||'').replace(/_/g,' ').toUpperCase()} — ${h.machine_id||''}</div>
        <div class="healing-desc">${escHtml(h.description||'Self-healing action applied')}</div>
        <div style="font-size:10px;color:var(--text-muted);margin-top:2px">${formatTime(h.timestamp)}</div>
      </div>
    </div>
  `).join('') || '<div style="padding:12px;font-size:12px;color:var(--text-muted)">No active healing</div>';
}

// ─── Defect Detection ─────────────────────────────────────────────────────────
function handleDefect(data) {
  APP.defects.unshift(data);
  if (APP.defects.length > 50) APP.defects.pop();
  renderDefect(data);
}

function renderDefect(defect) {
  const cameraView = document.getElementById('defect-camera');
  const statsEl = document.getElementById('defect-stats');
  if (cameraView) {
    const bb = defect.bounding_box;
    const defectType = defect.defect_type || 'Unknown';
    const conf = ((defect.confidence || 0) * 100).toFixed(1);
    cameraView.innerHTML = `
      <div style="position:relative;width:100%;height:100%;background:#0A1628;display:flex;align-items:center;justify-content:center">
        <div style="color:rgba(255,255,255,0.3);font-size:12px">Product inspection feed</div>
        ${defect.defect_found && bb ? `
          <div class="defect-bbox" style="left:${bb.x1*100}%;top:${bb.y1*100}%;width:${(bb.x2-bb.x1)*100}%;height:${(bb.y2-bb.y1)*100}%">
            <span class="defect-bbox-label">${defectType} ${conf}%</span>
          </div>` : ''}
        <div style="position:absolute;top:8px;left:8px;font-size:10px;color:rgba(255,255,255,0.5)">
          YOLOv8 + SwinTransformer + MaskRCNN
        </div>
        <div style="position:absolute;bottom:8px;right:8px;font-size:10px;color:${defect.defect_found?'#F44336':'#4CAF50'}">
          ${defect.defect_found ? '🔴 DEFECT DETECTED' : '🟢 PASS'}
        </div>
      </div>
    `;
  }
  if (statsEl) {
    const total = defect.total_inspected || 0;
    const defects = defect.total_defects_found || 0;
    const rate = defect.defect_rate_pct || 0;
    statsEl.innerHTML = `
      <div class="sensor-row"><span class="sensor-label">Total Inspected</span><span class="sensor-value">${total.toLocaleString()}</span></div>
      <div class="sensor-row"><span class="sensor-label">Defects Found</span><span class="sensor-value text-danger">${defects.toLocaleString()}</span></div>
      <div class="sensor-row"><span class="sensor-label">Defect Rate</span><span class="sensor-value ${rate > 5 ? 'critical' : rate > 2 ? 'warning' : ''}">${rate.toFixed(2)}%</span></div>
      ${defect.defect_found ? `
        <div class="sensor-row"><span class="sensor-label">Last Defect</span><span class="sensor-value text-danger">${(defect.defect_type||'').replace(/_/g,' ')}</span></div>
        <div class="sensor-row"><span class="sensor-label">Confidence</span><span class="sensor-value">${((defect.confidence||0)*100).toFixed(1)}%</span></div>
        <div class="sensor-row"><span class="sensor-label">Severity</span><span class="sensor-value ${defect.severity||''}">${defect.severity||'—'}</span></div>
      ` : ''}
    `;
  }
}

// ─── Incident Timeline ────────────────────────────────────────────────────────
function handleIncidents(data) {
  if (data.events) {
    APP.incidents = data.events;
    renderTimeline();
  }
}

function renderTimeline() {
  const container = document.getElementById('timeline-list');
  if (!container) return;
  container.innerHTML = APP.incidents.slice(0, 25).map(e => `
    <div class="timeline-event fade-in">
      <div class="timeline-icon">${e.icon||'📌'}</div>
      <div class="timeline-time">${e.time_display||formatTime(e.timestamp)}</div>
      <div class="timeline-desc">${escHtml(e.description||'')}</div>
      <div class="timeline-severity ${e.severity||'info'}">${e.severity||''}</div>
    </div>
  `).join('') || '<div style="padding:12px;font-size:12px;color:var(--text-muted)">No events yet</div>';
}

// ─── Efficiency Score ─────────────────────────────────────────────────────────
function handleEfficiency(data) {
  APP.efficiency = data;
  setEl('eff-score-main', (data.factory_efficiency_score||0).toFixed(1) + '%');
  setEl('sidebar-eff', (data.factory_efficiency_score||0).toFixed(1) + '%');
  const comp = data.components || {};
  setEl('eff-utilization', (comp.machine_utilization||0).toFixed(1) + '%');
  setEl('eff-throughput', (comp.production_throughput||0).toFixed(1) + '%');
  setEl('eff-energy', (comp.energy_efficiency||0).toFixed(1) + '%');
  setEl('eff-downtime', (comp.downtime_score||0).toFixed(1) + '%');
  setEl('eff-risk', data.raw_metrics?.failure_risk||'Low');
}

// ─── Root Cause Analysis ──────────────────────────────────────────────────────
function handleRCA(data) {
  if (data.machine_id) APP.rootCauses[data.machine_id] = data;
  renderRCA(data);
}

function renderRCA(rca) {
  const container = document.getElementById('rca-container');
  if (!container || !rca.causal_chain) return;
  container.innerHTML = `
    <div style="margin-bottom:8px">
      <strong>${rca.machine_name||rca.machine_id}</strong> — ${(rca.failure_mode||'').replace(/_/g,' ')}
      <span class="panel-badge danger" style="margin-left:6px">${(rca.failure_probability||0).toFixed(1)}%</span>
    </div>
    <div class="rca-chain">
      ${(rca.causal_chain||[]).map(step => `
        <div class="rca-step">
          <div class="rca-dot ${step.type||'intermediate'}">${step.step}</div>
          <div class="rca-text">${escHtml(step.description||'')}</div>
        </div>
      `).join('')}
    </div>
    ${rca.narrative ? `<div style="font-size:11px;color:var(--text-secondary);margin-top:8px;padding:8px;background:var(--bg);border-radius:6px">${escHtml(rca.narrative)}</div>` : ''}
  `;
}

// ─── Production Optimization ──────────────────────────────────────────────────
function handleOptimization(data) {
  APP.optimizationRecs = data;
  renderOptimization(data);
}

function renderOptimization(data) {
  const container = document.getElementById('optimization-container');
  if (!container) return;
  const bottleneck = data.bottleneck_machine;
  const recs = data.recommendations || [];
  container.innerHTML = `
    ${bottleneck ? `
      <div class="bottleneck-indicator">
        <span style="font-size:16px">⚠️</span>
        <span><strong>Bottleneck:</strong> ${bottleneck} — constraining production throughput</span>
      </div>
    ` : ''}
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px">
      AI Recommendations
    </div>
    ${recs.slice(0,5).map(r => `
      <div class="recommendation-item">
        <span>💡</span>
        <span>${escHtml(r)}</span>
      </div>
    `).join('')}
    ${data.rl_action ? `
      <div style="margin-top:8px;font-size:11px;background:rgba(25,118,210,0.05);border:1px solid rgba(25,118,210,0.1);border-radius:6px;padding:8px">
        <strong>RL Action:</strong> ${escHtml(data.rl_action)}
      </div>
    ` : ''}
  `;
}

function handleScenarioUpdate(data) {
  APP.activeScenarios = data.active || APP.activeScenarios;
  renderScenarioBadges();
}

function renderScenarioBadges() {
  const container = document.getElementById('active-scenarios');
  if (!container) return;
  if (!APP.activeScenarios || APP.activeScenarios.length === 0) {
    container.innerHTML = '<span style="font-size:12px;color:var(--text-muted)">No active scenarios</span>';
    return;
  }
  container.innerHTML = APP.activeScenarios.map(s =>
    `<span class="panel-badge danger">${(s.scenario_type||s).replace(/_/g,' ')}</span>`
  ).join(' ');
}

function updateFactoryStatus(factory) {
  if (!factory) return;
  const badge = document.getElementById('factory-status-badge');
  if (badge) {
    const status = factory.status || 'running';
    badge.textContent = status.toUpperCase();
    badge.className = 'status-badge ' + (status === 'running' ? '' : status === 'warning' ? 'warning' : 'critical');
  }
}

// ─── Charts Init ──────────────────────────────────────────────────────────────
function initCharts() {
  APP.charts.initProductionChart('chart-production');
  APP.charts.initMachineHealthChart('chart-machine-health');
  APP.charts.initBarChart('chart-utilization', ['M1','M2','M3','M4','M5']);
  APP.charts.initRadarChart('chart-radar');
  APP.charts.initSensorChart('chart-temp-m1', 'Temperature °C', '#E53935', 100);
  APP.charts.initSensorChart('chart-vib-m1', 'Vibration mm/s', '#F57F17', 15);
}

// ─── 3D Twin Init ─────────────────────────────────────────────────────────────
function initTwin() {
  if (typeof THREE === 'undefined') return;
  APP.twin = new DigitalTwin3D('twin-canvas-container');
  // Initialize when view is shown
}

function showTwin() {
  if (APP.twin && !APP.twin._initialized) {
    setTimeout(() => {
      APP.twin.init();
    }, 100);
  }
}

// ─── Navigation ───────────────────────────────────────────────────────────────
function initNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const view = item.dataset.view;
      if (!view) return;
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      document.querySelectorAll('.view').forEach(v => {
        v.style.display = 'none';
        v.classList.remove('active');
      });
      const targetView = document.getElementById('view-' + view);
      if (targetView) {
        targetView.style.display = view === 'twin' ? 'flex' : '';
        targetView.classList.add('active');
        if (view === 'twin') showTwin();
      }
      APP.activeView = view;
    });
  });
}

// ─── Scenario Controls ────────────────────────────────────────────────────────
function initScenarioButtons() {
  document.querySelectorAll('.scenario-btn[data-scenario]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const scenario = btn.dataset.scenario;
      const machine = btn.dataset.machine || null;
      try {
        const res = await fetch(`${API_BASE}/api/scenarios/trigger`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario_type: scenario, machine_id: machine, intensity: 1.0, duration_seconds: 30 })
        });
        const data = await res.json();
        if (data.success !== false) {
          btn.classList.add('active');
          setTimeout(() => btn.classList.remove('active'), 35000);
        }
      } catch (e) { console.warn('Scenario trigger error:', e); }
    });
  });

  const stopAllBtn = document.getElementById('stop-all-scenarios');
  if (stopAllBtn) {
    stopAllBtn.addEventListener('click', async () => {
      try {
        await fetch(`${API_BASE}/api/scenarios/stop-all`, { method: 'POST' });
        document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
      } catch (e) {}
    });
  }

  const resetBtn = document.getElementById('reset-factory-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      try {
        await fetch(`${API_BASE}/api/factory/reset`, { method: 'POST' });
      } catch (e) {}
    });
  }

  // Twin controls
  document.getElementById('btn-heatmap')?.addEventListener('click', function() {
    const active = this.classList.toggle('active');
    if (APP.twin) APP.twin.toggleHeatmap(active);
  });
  document.getElementById('btn-pipelines')?.addEventListener('click', function() {
    const active = this.classList.toggle('active');
    if (APP.twin) APP.twin.togglePipelines(active);
  });
  document.getElementById('btn-reset-cam')?.addEventListener('click', () => {
    if (APP.twin) APP.twin.resetCamera();
  });
}

// ─── Initial data load ────────────────────────────────────────────────────────
async function loadInitialData() {
  try {
    const [stateRes, incidentRes, lifecycleRes] = await Promise.all([
      fetch(`${API_BASE}/api/factory/state`).catch(() => null),
      fetch(`${API_BASE}/api/incidents`).catch(() => null),
      fetch(`${API_BASE}/api/lifecycle`).catch(() => null),
    ]);
    if (stateRes?.ok) {
      const state = await stateRes.json();
      handleSensorUpdate(state);
    }
    if (incidentRes?.ok) {
      const incidents = await incidentRes.json();
      APP.incidents = incidents.events || [];
      renderTimeline();
    }
    if (lifecycleRes?.ok) {
      const lc = await lifecycleRes.json();
      APP.lifecycle = lc.lifecycle || {};
      renderLifecycle();
    }
  } catch (e) { console.warn('Initial load error:', e); }
}

function renderLifecycle() {
  const tbody = document.getElementById('lifecycle-tbody');
  if (!tbody) return;
  tbody.innerHTML = Object.values(APP.lifecycle).map(lc => `
    <tr>
      <td><strong>${lc.machine_id}</strong></td>
      <td>${lc.machine_name}</td>
      <td>${(lc.runtime_hours||0).toLocaleString()}h</td>
      <td>
        <div style="display:flex;align-items:center;gap:6px">
          <div style="flex:1;height:6px;background:#EEE;border-radius:3px">
            <div style="width:${lc.health_score||0}%;height:100%;border-radius:3px;background:${lc.health_score>=70?'var(--success)':lc.health_score>=40?'var(--warning)':'var(--danger)'}"></div>
          </div>
          <span style="font-size:11px;font-weight:600">${(lc.health_score||0).toFixed(0)}%</span>
        </div>
      </td>
      <td>${lc.predicted_remaining_life_months} mo</td>
      <td>${lc.last_maintenance_date||'—'}</td>
      <td>${lc.next_maintenance_due||'—'}</td>
      <td>${lc.total_failures||0}</td>
    </tr>
  `).join('');
}

// ─── Clock ────────────────────────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById('clock');
  if (!el) return;
  const tick = () => {
    el.textContent = new Date().toLocaleTimeString();
  };
  tick();
  setInterval(tick, 1000);
}

// ─── Utility ──────────────────────────────────────────────────────────────────
function setEl(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setElStyle(id, prop, value) {
  const el = document.getElementById(id);
  if (el) el.style[prop] = value;
}

function getSensorClass(val, warn, crit) {
  if (val >= crit) return 'crit';
  if (val >= warn) return 'warn';
  return 'ok';
}

function formatTime(ts) {
  if (!ts) return '';
  try { return new Date(ts).toLocaleTimeString(); } catch (e) { return ''; }
}

function escHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
