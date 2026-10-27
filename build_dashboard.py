import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "dashboard_data" / "dashboard_data.json"
HSI_PATH = Path(__file__).parent / "dashboard_data" / "hyperspectral_images.json"
OUT_PATH = Path(__file__).parent / "TRACE_demo_dashboard.html"

data = json.load(open(DATA_PATH))
hsi_data = json.load(open(HSI_PATH))
DATA_JSON = json.dumps(data)
HSI_JSON = json.dumps(hsi_data)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TRACE - POAO Cold-Chain Monitoring Demo</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
<style>
:root{
  --navy:#0d1b2a; --navy2:#13263b; --blue:#3a6ea5; --blue-light:#6fa3d8;
  --bg:#f4f7fa; --card:#ffffff; --text:#1c2b3a; --text-sec:#5c7185;
  --ok:#2e9e5b; --warn:#e0973a; --crit:#d1473f; --gap:18px; --radius:12px;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;}
.wrap{max-width:1440px;margin:0 auto;padding:20px;}
.header{background:linear-gradient(135deg,var(--navy) 0%,var(--navy2) 60%,var(--blue) 140%);color:#fff;border-radius:var(--radius);padding:26px 30px;margin-bottom:var(--gap);position:relative;overflow:hidden;}
.header::after{content:"";position:absolute;right:-60px;top:-60px;width:220px;height:220px;background:radial-gradient(circle,rgba(111,163,216,0.35) 0%,transparent 70%);}
.header .badge{display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);padding:4px 12px;border-radius:20px;font-size:11px;letter-spacing:0.5px;text-transform:uppercase;margin-bottom:10px;}
.header h1{font-size:26px;font-weight:700;margin-bottom:6px;}
.header p{font-size:14px;color:rgba(255,255,255,0.8);max-width:820px;}
.header .meta{margin-top:14px;display:flex;gap:22px;flex-wrap:wrap;font-size:12.5px;color:rgba(255,255,255,0.75);}
.report-btn{margin-top:18px;background:#fff;color:var(--navy);border:none;padding:11px 20px;border-radius:8px;font-size:13.5px;font-weight:700;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.15);}
.report-btn:hover{background:#eef3f9;}
.header .meta b{color:#fff;}

.kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:var(--gap);margin-bottom:var(--gap);}
.kpi{background:var(--card);border-radius:var(--radius);padding:18px 20px;box-shadow:0 1px 4px rgba(13,27,42,0.08);border-left:4px solid var(--blue);}
.kpi.ok{border-left-color:var(--ok);} .kpi.warn{border-left-color:var(--warn);} .kpi.crit{border-left-color:var(--crit);}
.kpi-label{font-size:11.5px;color:var(--text-sec);text-transform:uppercase;letter-spacing:0.6px;margin-bottom:6px;font-weight:600;}
.kpi-value{font-size:26px;font-weight:700;color:var(--navy);}
.kpi-sub{font-size:12px;color:var(--text-sec);margin-top:4px;}

.grid2{display:grid;grid-template-columns:1.4fr 1fr;gap:var(--gap);margin-bottom:var(--gap);}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--gap);margin-bottom:var(--gap);}
.card{background:var(--card);border-radius:var(--radius);padding:20px 22px;box-shadow:0 1px 4px rgba(13,27,42,0.08);}
.card h3{font-size:14.5px;font-weight:700;color:var(--navy);margin-bottom:2px;}
.card .card-sub{font-size:12px;color:var(--text-sec);margin-bottom:14px;}
.card canvas{max-height:280px;}

.heatmap-wrap{overflow-x:auto;}
.heatmap-grid{display:grid;gap:2px;}
.heatmap-row-label{font-size:10.5px;color:var(--text-sec);padding-right:6px;white-space:nowrap;display:flex;align-items:center;justify-content:flex-end;}
.heatmap-cell{width:100%;aspect-ratio:1/1;border-radius:2px;}
.heatmap-legend{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:11px;color:var(--text-sec);}
.legend-gradient{width:120px;height:10px;border-radius:5px;background:linear-gradient(90deg,#8c2f2f,#e0973a,#e8d477,#4f9e6e);}

.badge-sev{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11.5px;font-weight:700;color:#fff;}

.hsi-controls{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;margin:14px 0;}
.hsi-select-group{display:flex;align-items:center;gap:8px;}
.hsi-select-group label{font-size:12px;color:var(--text-sec);font-weight:600;}
.hsi-select-group select{padding:7px 10px;border:1px solid #d7dee6;border-radius:6px;font-size:13px;background:#fff;color:var(--text);}
.hsi-tabs{display:flex;gap:6px;flex-wrap:wrap;}
.hsi-tab{padding:7px 14px;border-radius:20px;font-size:12.5px;font-weight:600;background:#eef3f9;color:var(--text-sec);cursor:pointer;border:1px solid transparent;white-space:nowrap;}
.hsi-tab.active{background:var(--navy);color:#fff;}
.hsi-body{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start;}
.hsi-image-wrap{max-width:420px;margin:0 auto;}
.hsi-image-panel .heatmap-grid{grid-template-columns:repeat(20, 1fr);gap:1px;}
.hsi-image-panel .heatmap-cell{border-radius:0;}
.hsi-stats{display:flex;gap:18px;margin-top:14px;justify-content:center;flex-wrap:wrap;}
.hsi-stat{text-align:center;}
.hsi-stat .v{font-size:20px;font-weight:800;color:var(--navy);}
.hsi-stat .l{font-size:10.5px;color:var(--text-sec);text-transform:uppercase;letter-spacing:0.4px;}
.hsi-stat.crit .v{color:var(--crit);}
.hsi-corrupted-banner{background:#fdecea;color:var(--crit);border-radius:8px;padding:8px 12px;font-size:12px;font-weight:600;text-align:center;margin-top:10px;}
@media(max-width:900px){.hsi-body{grid-template-columns:1fr}}
.badge-sev.Critical{background:var(--crit);}
.badge-sev.Warning{background:var(--warn);}
.badge-sev.Info{background:var(--blue);}
.badge-risk{display:inline-block;padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700;}
.badge-risk.High{background:#fbe1df;color:var(--crit);}
.badge-risk.Medium{background:#fbedd9;color:#a9660f;}
.badge-risk.Low{background:#dff2e6;color:var(--ok);}
.badge-risk.DataQualityIssue,.badge-risk.Data{background:#e3edf9;color:var(--blue);}

table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
.data-table thead th{text-align:left;padding:9px 10px;border-bottom:2px solid #e3e8ee;color:var(--text-sec);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.4px;}
.data-table tbody td{padding:9px 10px;border-bottom:1px solid #f0f2f5;}
.data-table tbody tr:hover{background:#f7fafc;}

.note{background:#eef3f9;border-left:4px solid var(--blue);border-radius:8px;padding:14px 18px;font-size:13px;color:var(--text-sec);margin-bottom:var(--gap);}
.note b{color:var(--navy);}

.pipeline{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.pipeline-step{background:var(--navy);color:#fff;font-size:11.5px;padding:8px 12px;border-radius:8px;flex:1;min-width:130px;text-align:center;}
.pipeline-step .n{font-weight:800;color:var(--blue-light);display:block;font-size:10px;letter-spacing:1px;margin-bottom:3px;}

.footer{text-align:center;font-size:12px;color:var(--text-sec);padding:22px 0 8px;}

@media(max-width:1100px){.kpi-row{grid-template-columns:repeat(2,1fr)}.grid2,.grid3{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <span class="badge">TRACE &middot; PEACEPLUS Cross-Border Programme</span>
    <h1>POAO Cold-Chain Monitoring Dashboard</h1>
    <p>A demo I put together for the TRACE interview. It follows six fictional cross-border SMEs shipping products of animal origin between Northern Ireland and Ireland, using IoT sensors and hyperspectral imaging to keep an eye on the cold chain. It's built around the pilot setup, monitoring, and reporting work described in the job listing.</p>
    <div class="meta">
      <span><b id="m-shipments">-</b> shipments simulated</span>
      <span><b id="m-smes">-</b> cross-border SMEs</span>
      <span><b id="m-readings">-</b> sensor readings (15 min intervals, 48 hour journeys)</span>
      <span><b>Data:</b> synthetic, for demo purposes</span>
    </div>
    <button class="report-btn" onclick="window.__downloadReport()">&#128196; Generate &amp; Download Monitoring Report</button>
  </div>

  <div class="kpi-row">
    <div class="kpi"><div class="kpi-label">Shipments Monitored</div><div class="kpi-value" id="kpi-ship">-</div><div class="kpi-sub" id="kpi-ship-sub">across 6 SMEs</div></div>
    <div class="kpi ok"><div class="kpi-label">Compliance Rate</div><div class="kpi-value" id="kpi-comp">-</div><div class="kpi-sub">within cold-chain threshold</div></div>
    <div class="kpi crit"><div class="kpi-label">High-Status Shipments</div><div class="kpi-value" id="kpi-high">-</div><div class="kpi-sub" id="kpi-high-sub">flagged for QA action</div></div>
    <div class="kpi"><div class="kpi-label">Avg. Excursion Duration</div><div class="kpi-value" id="kpi-acc">-</div><div class="kpi-sub">per shipment, above threshold</div></div>
    <div class="kpi warn"><div class="kpi-label">Active Alerts</div><div class="kpi-value" id="kpi-alerts">-</div><div class="kpi-sub">critical + warning + info</div></div>
  </div>

  <div class="note">
    <b>What this covers:</b> the monitoring and reporting work described in the job listing. Pilot IoT sensors and hyperspectral imaging feed into real-time dashboards, threshold-based compliance alerts, a risk register, and inputs for quarterly SEUPB reporting. There's no predictive modelling here. Every status you see comes straight from the compliance thresholds set for each POAO product category.
    <div class="pipeline">
      <div class="pipeline-step"><span class="n">STEP 1</span>15 min IoT and hyperspectral capture</div>
      <div class="pipeline-step"><span class="n">STEP 2</span>Downsample to 1 hour monitoring windows</div>
      <div class="pipeline-step"><span class="n">STEP 3</span>Apply product-specific compliance thresholds</div>
      <div class="pipeline-step"><span class="n">STEP 4</span>Rule-based alerts and risk register</div>
      <div class="pipeline-step"><span class="n">STEP 5</span>Dashboard and reporting outputs</div>
    </div>
  </div>

  <div class="grid2">
    <div class="card">
      <h3 id="ts-title">Example Shipment: Temperature &amp; Freshness Index</h3>
      <div class="card-sub" id="ts-sub"></div>
      <canvas id="chart-timeseries" height="110"></canvas>
    </div>
    <div class="card">
      <h3>In-Transit Spectral Sensor Trend (8 bands)</h3>
      <div class="card-sub">This comes from a fixed-point IoT sensor reading continuously every 15 minutes. It's not imaging, just a single-point reflectance trend over the journey.</div>
      <div class="heatmap-wrap"><div id="heatmap"></div></div>
      <div class="heatmap-legend"><span>Degraded</span><div class="legend-gradient"></div><span>Fresh</span></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:var(--gap)">
    <h3>Hyperspectral Imaging: Checkpoint Inspection</h3>
    <div class="card-sub">This is the actual imaging layer. A hyperspectral camera captures a pixel grid over the pallet or product surface at each physical hand-off point. Every pixel carries its own 8-band spectral signature, which gets reduced to a per-pixel Quality Index using an NDVI-style band ratio. A simple threshold rule (basic computer vision, no machine learning) flags degraded pixels and reports the defect area as a percentage.</div>

    <div class="hsi-controls">
      <div class="hsi-select-group">
        <label>Shipment</label>
        <select id="hsi-shipment-select" onchange="window.__hsiRender()"></select>
      </div>
      <div class="hsi-tabs" id="hsi-checkpoint-tabs"></div>
    </div>

    <div class="hsi-body">
      <div class="hsi-image-panel">
        <div class="hsi-image-wrap"><div id="hsi-image-grid" class="heatmap-grid"></div></div>
        <div class="heatmap-legend"><span>Degraded / Flagged</span><div class="legend-gradient"></div><span>Fresh</span></div>
        <div class="hsi-stats" id="hsi-stats"></div>
      </div>
      <div class="hsi-spectral-panel">
        <div class="card-sub" style="margin-bottom:8px">Average spectral signature for normal versus flagged pixel regions at this checkpoint</div>
        <canvas id="chart-hsi-signature" height="220"></canvas>
      </div>
    </div>
  </div>

  <div class="grid3">
    <div class="card">
      <h3>Avg. Threshold Breach % by SME</h3>
      <div class="card-sub">Share of monitoring windows above the compliance threshold, per shipment, averaged per SME</div>
      <canvas id="chart-sme-risk"></canvas>
    </div>
    <div class="card">
      <h3>Product Type Breakdown</h3>
      <div class="card-sub">Shipments simulated by POAO category</div>
      <canvas id="chart-product"></canvas>
    </div>
    <div class="card">
      <h3>Monitoring Status Breakdown</h3>
      <div class="card-sub">Rule-based status across all monitored shipments</div>
      <canvas id="chart-status"></canvas>
    </div>
  </div>

  <div class="card" style="margin-bottom:var(--gap)">
    <h3>Fleet-Wide Compliance Trend</h3>
    <div class="card-sub">Hourly compliance rate and average freshness index across all monitored shipments over the 48-hour window</div>
    <canvas id="chart-fleet-trend" height="70"></canvas>
  </div>

  <div class="card" style="margin-bottom:var(--gap)">
    <h3>Live Alerts Feed</h3>
    <div class="card-sub">Generated automatically from the threshold rules and ranked by severity, ready to send to the SME and Project Manager.</div>
    <div style="overflow-x:auto"><table class="data-table" id="alerts-table"></table></div>
  </div>

  <div class="card">
    <h3>Shipment Monitoring Register</h3>
    <div class="card-sub">Every simulated shipment, sortable by breach percentage, feeding straight into the project risk register.</div>
    <div style="overflow-x:auto"><table class="data-table" id="shipment-table"></table></div>
  </div>

  <div class="footer">TRACE candidate demo. Synthetic data generated for interview purposes. Pipeline: Python (pandas, scikit-learn) to JSON to this interactive HTML dashboard.</div>
</div>

<script>
const DATA = __DATA_JSON__;
const HSI = __HSI_JSON__;
const NAVY = '#0d1b2a', BLUE='#3a6ea5', BLUE_L='#6fa3d8', OK='#2e9e5b', WARN='#e0973a', CRIT='#d1473f', PURP='#8172B3', BROWN='#937860';
const PALETTE = [BLUE, OK, WARN, CRIT, PURP, BROWN, BLUE_L];

function fmtPct(x){ return x.toFixed(1) + '%'; }

// ---------- Header / KPIs ----------
document.getElementById('m-shipments').textContent = DATA.kpis.total_shipments;
document.getElementById('m-smes').textContent = DATA.kpis.total_smes;
document.getElementById('m-readings').textContent = DATA.kpis.total_sensor_readings.toLocaleString();

document.getElementById('kpi-ship').textContent = DATA.kpis.total_shipments;
document.getElementById('kpi-ship-sub').textContent = 'across ' + DATA.kpis.total_smes + ' SMEs';
document.getElementById('kpi-comp').textContent = fmtPct(DATA.kpis.compliance_rate_pct);
document.getElementById('kpi-high').textContent = DATA.kpis.high_status;
document.getElementById('kpi-high-sub').textContent = DATA.kpis.medium_status + ' additional warnings, ' + DATA.kpis.data_quality_status + ' data-quality issues';
document.getElementById('kpi-acc').textContent = DATA.kpis.avg_breach_minutes + ' min';
document.getElementById('kpi-alerts').textContent = DATA.alerts.length;

Chart.defaults.font.family = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif";
Chart.defaults.color = '#5c7185';

// ---------- Time series chart ----------
const es = DATA.example_series;
document.getElementById('ts-title').textContent = `Shipment ${es.shipment_id}, ${es.sme_name} (${es.product})`;
document.getElementById('ts-sub').textContent = `Compliance threshold: ${es.threshold}°C. You can see the cold-chain breach visibly degrade the Freshness Index.`;

new Chart(document.getElementById('chart-timeseries').getContext('2d'), {
  data: {
    labels: es.timestamps,
    datasets: [
      {
        type: 'line', label: 'Temperature (°C)', data: es.temperature,
        borderColor: CRIT, backgroundColor: CRIT+'20', yAxisID: 'y', tension: 0.25, pointRadius: 0, borderWidth: 2,
      },
      {
        type: 'line', label: 'Compliance Threshold', data: es.timestamps.map(()=>es.threshold),
        borderColor: '#94a3b8', borderDash: [6,4], yAxisID: 'y', pointRadius: 0, borderWidth: 1.5,
      },
      {
        type: 'line', label: 'Freshness Index', data: es.freshness_index,
        borderColor: OK, backgroundColor: OK+'20', yAxisID: 'y1', tension: 0.25, pointRadius: 0, borderWidth: 2, fill: true,
      },
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 16, boxWidth: 8 } } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
      y: { position: 'left', title: { display: true, text: 'Temperature (°C)' }, grid: { color: '#eef1f4' } },
      y1: { position: 'right', min: 0, max: 1, title: { display: true, text: 'Freshness Index' }, grid: { display: false } },
    }
  }
});

// ---------- Hyperspectral heatmap (custom grid) ----------
(function(){
  const bands = es.band_labels;
  const times = es.timestamps;
  const step = Math.max(1, Math.floor(times.length/40)); // thin out columns for readability
  const cols = [];
  for(let i=0;i<times.length;i+=step) cols.push(i);

  const container = document.getElementById('heatmap');
  container.innerHTML = '';
  const grid = document.createElement('div');
  grid.className = 'heatmap-grid';
  grid.style.gridTemplateColumns = `70px repeat(${cols.length}, minmax(10px, 1fr))`;
  container.appendChild(grid);

  // top-left corner blank
  grid.appendChild(document.createElement('div'));
  // time header row (sparse labels)
  cols.forEach((ci, idx) => {
    const lbl = document.createElement('div');
    lbl.style.fontSize = '9px'; lbl.style.color = '#5c7185'; lbl.style.textAlign='center';
    lbl.textContent = (idx % 4 === 0) ? times[ci] : '';
    grid.appendChild(lbl);
  });

  function colorFor(v){
    // v in [0,1] reflectance -> map low=degraded(red/orange), high=fresh(green), via band value normalized per-band
    const r = Math.round(140 + (1-v)*100);
    const g = Math.round(60 + v*140);
    const b = Math.round(60 + v*60);
    return `rgb(${r},${g},${b})`;
  }

  bands.forEach(band => {
    const rowLabel = document.createElement('div');
    rowLabel.className = 'heatmap-row-label';
    rowLabel.textContent = band;
    grid.appendChild(rowLabel);
    const vals = es.spectral_bands[band];
    const maxV = Math.max(...vals), minV = Math.min(...vals);
    cols.forEach(ci => {
      const cell = document.createElement('div');
      cell.className = 'heatmap-cell';
      const raw = vals[ci];
      const norm = maxV > minV ? (raw - minV)/(maxV-minV) : 0.5;
      cell.style.background = colorFor(norm);
      cell.title = `${band} @ ${times[ci]}: ${raw.toFixed(3)}`;
      grid.appendChild(cell);
    });
  });
})();

// ---------- Hyperspectral IMAGING viewer (spatial checkpoint images) ----------
(function(){
  const shipmentKeys = Object.keys(HSI.shipments); // e.g. high, medium, low, sensor_fault
  const select = document.getElementById('hsi-shipment-select');
  const labelFor = (key) => {
    const s = HSI.shipments[key];
    return `${s.shipment_id}, ${s.sme_name} (${s.risk_label})`;
  };
  shipmentKeys.forEach(key => {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = labelFor(key);
    select.appendChild(opt);
  });
  // default to the "high" risk shipment so the demo opens on the most interesting case
  select.value = shipmentKeys.includes('high') ? 'high' : shipmentKeys[0];

  let activeCheckpoint = 0;
  let hsiChart = null;

  function qualityColor(v){
    // v in [0,1]: red/orange (degraded) -> yellow -> green (fresh)
    const r = Math.round(210 - v*130);
    const g = Math.round(70 + v*140);
    const b = Math.round(70 + v*40);
    return `rgb(${r},${g},${b})`;
  }

  function renderTabs(){
    const tabs = document.getElementById('hsi-checkpoint-tabs');
    tabs.innerHTML = '';
    HSI.checkpoints.forEach((cp, idx) => {
      const el = document.createElement('div');
      el.className = 'hsi-tab' + (idx === activeCheckpoint ? ' active' : '');
      el.textContent = `${idx+1}. ${cp}`;
      el.onclick = () => { activeCheckpoint = idx; renderAll(); };
      tabs.appendChild(el);
    });
  }

  function renderImage(){
    const key = select.value;
    const ship = HSI.shipments[key];
    const cp = ship.checkpoints[activeCheckpoint];
    const grid = cp.quality_grid;
    const n = HSI.grid_size;

    const container = document.getElementById('hsi-image-grid');
    container.innerHTML = '';
    container.style.gridTemplateColumns = `repeat(${n}, 1fr)`;
    for(let i=0;i<n;i++){
      for(let j=0;j<n;j++){
        const cell = document.createElement('div');
        cell.className = 'heatmap-cell';
        const v = grid[i][j];
        cell.style.background = qualityColor(v);
        if(v < HSI.quality_threshold){
          cell.style.boxShadow = 'inset 0 0 0 1px rgba(209,71,63,0.55)';
        }
        cell.title = `Quality: ${v.toFixed(2)}`;
        container.appendChild(cell);
      }
    }

    const statsEl = document.getElementById('hsi-stats');
    const defectClass = cp.defect_pct > 10 ? 'crit' : '';
    statsEl.innerHTML = `
      <div class="hsi-stat ${defectClass}"><div class="v">${cp.defect_pct}%</div><div class="l">Defect Area</div></div>
      <div class="hsi-stat"><div class="v">${cp.mean_quality}</div><div class="l">Mean Quality Index</div></div>
      <div class="hsi-stat"><div class="v">${n}&times;${n}</div><div class="l">Pixels Captured</div></div>
    ` + (cp.corrupted_frame ? `<div class="hsi-corrupted-banner" style="width:100%">&#9888; Camera or sensor dropout detected at this checkpoint. This frame is flagged as unreliable and needs recalibration.</div>` : '');
  }

  function renderSignature(){
    const key = select.value;
    const ship = HSI.shipments[key];
    const cp = ship.checkpoints[activeCheckpoint];
    const ctx = document.getElementById('chart-hsi-signature').getContext('2d');
    if(hsiChart) hsiChart.destroy();
    hsiChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: HSI.bands.map(b => b + 'nm'),
        datasets: [
          { label: 'Normal pixels', data: cp.normal_signature, borderColor: OK, backgroundColor: OK+'20', borderWidth: 2, tension: 0.3, fill: false, spanGaps: true },
          { label: 'Flagged pixels', data: cp.flagged_signature, borderColor: CRIT, backgroundColor: CRIT+'20', borderWidth: 2, tension: 0.3, fill: false, borderDash: cp.flagged_signature.every(v=>v===null) ? [4,4] : [], spanGaps: true },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8 } } },
        scales: { x: { grid: { display: false } }, y: { title: { display: true, text: 'Reflectance' }, grid: { color: '#eef1f4' } } }
      }
    });
  }

  function renderAll(){
    renderTabs();
    renderImage();
    renderSignature();
  }

  select.onchange = () => { activeCheckpoint = 0; renderAll(); };
  window.__hsiRender = renderAll;
  renderAll();
})();

// ---------- SME breach % bar chart ----------
(function(){
  const entries = Object.entries(DATA.breach_pct_by_sme).sort((a,b)=>b[1]-a[1]);
  new Chart(document.getElementById('chart-sme-risk').getContext('2d'), {
    type: 'bar',
    data: {
      labels: entries.map(e=>e[0]),
      datasets: [{ data: entries.map(e=>e[1]), backgroundColor: entries.map((_,i)=>PALETTE[i%PALETTE.length]+'CC'), borderRadius: 4 }]
    },
    options: {
      responsive:true, maintainAspectRatio:false, indexAxis:'y',
      plugins:{legend:{display:false}},
      scales:{ x:{ beginAtZero:true, max:1, grid:{color:'#eef1f4'} }, y:{ grid:{display:false} } }
    }
  });
})();

// ---------- Product doughnut ----------
(function(){
  const entries = Object.entries(DATA.product_breakdown);
  new Chart(document.getElementById('chart-product').getContext('2d'), {
    type: 'doughnut',
    data: { labels: entries.map(e=>e[0]), datasets:[{ data: entries.map(e=>e[1]), backgroundColor: PALETTE.map(c=>c+'CC'), borderColor:'#fff', borderWidth:2 }]},
    options: { responsive:true, maintainAspectRatio:false, cutout:'62%', plugins:{legend:{position:'right', labels:{usePointStyle:true, boxWidth:8}}} }
  });
})();

// ---------- Monitoring status doughnut ----------
(function(){
  const labels = ['Low', 'Medium', 'High', 'Data Quality Issue'];
  const values = [DATA.kpis.low_status, DATA.kpis.medium_status, DATA.kpis.high_status, DATA.kpis.data_quality_status];
  const colors = [OK+'CC', WARN+'CC', CRIT+'CC', BLUE+'CC'];
  new Chart(document.getElementById('chart-status').getContext('2d'), {
    type: 'doughnut',
    data: { labels, datasets:[{ data: values, backgroundColor: colors, borderColor:'#fff', borderWidth:2 }]},
    options: { responsive:true, maintainAspectRatio:false, cutout:'62%', plugins:{legend:{position:'right', labels:{usePointStyle:true, boxWidth:8}}} }
  });
})();

// ---------- Fleet-wide compliance trend ----------
(function(){
  const t = DATA.fleet_hourly_trend;
  new Chart(document.getElementById('chart-fleet-trend').getContext('2d'), {
    data: {
      labels: t.hour.map(h => 'H+' + h),
      datasets: [
        { type:'line', label:'Compliance Rate (%)', data: t.compliance_pct, borderColor: OK, backgroundColor: OK+'20', yAxisID:'y', tension:0.25, pointRadius:0, borderWidth:2, fill:true },
        { type:'line', label:'Avg Freshness Index', data: t.avg_freshness, borderColor: BLUE, backgroundColor: BLUE+'20', yAxisID:'y1', tension:0.25, pointRadius:0, borderWidth:2 },
      ]
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      interaction:{mode:'index', intersect:false},
      plugins:{legend:{position:'top', labels:{usePointStyle:true, padding:16, boxWidth:8}}},
      scales:{
        x:{ grid:{display:false}, ticks:{maxTicksLimit:16} },
        y:{ position:'left', min:0, max:100, title:{display:true, text:'Compliance Rate (%)'}, grid:{color:'#eef1f4'} },
        y1:{ position:'right', min:0, max:1, title:{display:true, text:'Freshness Index'}, grid:{display:false} },
      }
    }
  });
})();

// ---------- Alerts table ----------
(function(){
  let html = '<thead><tr><th>Shipment</th><th>SME</th><th>Product</th><th>Route</th><th>Breach %</th><th>Max Temp</th><th>Min Freshness</th><th>Severity</th><th>Recommended Action</th></tr></thead><tbody>';
  DATA.alerts.forEach(a => {
    html += `<tr>
      <td>${a.shipment_id}</td><td>${a.sme_name}</td><td>${a.product}</td><td>${a.route}</td>
      <td>${(a.breach_pct*100).toFixed(0)}%</td><td>${a.max_temp.toFixed(1)}°C</td><td>${a.min_freshness.toFixed(2)}</td>
      <td><span class="badge-sev ${a.severity}">${a.severity}</span></td>
      <td style="max-width:280px">${a.recommended_action}</td>
    </tr>`;
  });
  html += '</tbody>';
  document.getElementById('alerts-table').innerHTML = html;
})();

// ---------- Shipment monitoring register (sortable) ----------
(function(){
  const cols = [
    {f:'shipment_id', l:'Shipment'}, {f:'sme_name', l:'SME'}, {f:'product', l:'Product'},
    {f:'route', l:'Route'}, {f:'breach_pct', l:'Breach %'}, {f:'max_temp', l:'Max Temp (°C)'},
    {f:'excursion_minutes', l:'Excursion (min)'}, {f:'monitoring_status', l:'Status'},
  ];
  let sortCol = 'breach_pct', sortDir = 'desc';
  const container = document.getElementById('shipment-table');

  function render(){
    const sorted = [...DATA.shipment_monitoring_table].sort((a,b)=>{
      const av=a[sortCol], bv=b[sortCol];
      const cmp = av<bv?-1:av>bv?1:0;
      return sortDir==='asc'?cmp:-cmp;
    });
    let html = '<thead><tr>';
    cols.forEach(c => {
      const arrow = sortCol===c.f ? (sortDir==='asc'?' &#9650;':' &#9660;') : '';
      html += `<th style="cursor:pointer" onclick="window.__sortShip('${c.f}')">${c.l}${arrow}</th>`;
    });
    html += '</tr></thead><tbody>';
    sorted.forEach(r => {
      const statusClass = r.monitoring_status.replace(/\s/g,'');
      html += `<tr>
        <td>${r.shipment_id}</td><td>${r.sme_name}</td><td>${r.product}</td><td>${r.route}</td>
        <td>${(r.breach_pct*100).toFixed(1)}%</td><td>${r.max_temp.toFixed(1)}</td><td>${r.excursion_minutes}</td>
        <td><span class="badge-risk ${statusClass}">${r.monitoring_status}</span></td>
      </tr>`;
    });
    html += '</tbody>';
    container.innerHTML = html;
  }
  window.__sortShip = function(field){
    if(sortCol===field) sortDir = sortDir==='asc'?'desc':'asc'; else { sortCol = field; sortDir='desc'; }
    render();
  };
  render();
})();

// ---------- Generate & download monitoring report ----------
(function(){
  function buildReportHTML(){
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    const k = DATA.kpis;

    const topAlerts = DATA.alerts.slice(0, 10).map(a => `
      <tr>
        <td>${a.shipment_id}</td><td>${a.sme_name}</td><td>${a.product}</td><td>${a.route}</td>
        <td>${(a.breach_pct*100).toFixed(0)}%</td><td>${a.max_temp.toFixed(1)}&deg;C</td>
        <td><span class="sev sev-${a.severity}">${a.severity}</span></td>
        <td>${a.recommended_action}</td>
      </tr>`).join('');

    const registerRows = DATA.shipment_monitoring_table.map(r => `
      <tr>
        <td>${r.shipment_id}</td><td>${r.sme_name}</td><td>${r.product}</td><td>${r.route}</td>
        <td>${(r.breach_pct*100).toFixed(1)}%</td><td>${r.max_temp.toFixed(1)}</td><td>${r.excursion_minutes}</td><td>${r.monitoring_status}</td>
      </tr>`).join('');

    const productRows = Object.entries(DATA.product_breakdown).map(([p,v]) => `<tr><td>${p}</td><td>${v}</td></tr>`).join('');

    return `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>TRACE Monitoring Report - ${dateStr}</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1c2b3a;max-width:900px;margin:0 auto;padding:40px;line-height:1.5;}
  h1{font-size:22px;color:#0d1b2a;margin-bottom:2px;}
  h2{font-size:16px;color:#0d1b2a;border-bottom:2px solid #eef3f9;padding-bottom:6px;margin-top:34px;}
  .sub{color:#5c7185;font-size:13px;margin-bottom:24px;}
  .kpis{display:flex;gap:16px;flex-wrap:wrap;margin:18px 0 28px;}
  .kpi{background:#f4f7fa;border-left:4px solid #3a6ea5;border-radius:6px;padding:12px 16px;min-width:150px;}
  .kpi .v{font-size:22px;font-weight:800;color:#0d1b2a;}
  .kpi .l{font-size:11px;color:#5c7185;text-transform:uppercase;letter-spacing:.4px;}
  table{width:100%;border-collapse:collapse;font-size:12.5px;margin:10px 0 6px;}
  th{background:#0d1b2a;color:#fff;text-align:left;padding:7px 9px;font-size:11px;text-transform:uppercase;}
  td{padding:7px 9px;border-bottom:1px solid #eef1f4;}
  .sev{padding:2px 8px;border-radius:10px;font-size:10.5px;font-weight:700;color:#fff;}
  .sev-Critical{background:#d1473f;} .sev-Warning{background:#e0973a;} .sev-Info{background:#3a6ea5;}
  .disclaimer{margin-top:36px;background:#eef3f9;border-left:4px solid #3a6ea5;border-radius:6px;padding:12px 16px;font-size:12px;color:#5c7185;}
  .footer{margin-top:30px;font-size:11px;color:#98a4b0;text-align:center;}
  @media print{ body{padding:15px;} }
</style></head>
<body>
  <h1>TRACE POAO Cold-Chain Monitoring Report</h1>
  <div class="sub">Generated ${dateStr} &middot; Covers ${k.total_shipments} shipments across ${k.total_smes} cross-border SMEs &middot; Synthetic demo data</div>

  <h2>Summary</h2>
  <p>Over the monitored period, <b>${k.compliance_rate_pct}%</b> of shipments stayed fully within their cold-chain compliance threshold.
  <b>${k.high_status}</b> shipment(s) were flagged High status and need QA review or SME follow-up, <b>${k.medium_status}</b> were flagged Medium (a warning),
  and <b>${k.data_quality_status}</b> had a sensor or data-quality issue rather than a genuine product issue. Where a temperature excursion did happen,
  it lasted <b>${k.avg_breach_minutes} minutes</b> on average.</p>

  <div class="kpis">
    <div class="kpi"><div class="v">${k.total_shipments}</div><div class="l">Shipments Monitored</div></div>
    <div class="kpi"><div class="v">${k.compliance_rate_pct}%</div><div class="l">Compliance Rate</div></div>
    <div class="kpi"><div class="v">${k.high_status}</div><div class="l">High Status</div></div>
    <div class="kpi"><div class="v">${DATA.alerts.length}</div><div class="l">Active Alerts</div></div>
  </div>

  <h2>Priority Alerts</h2>
  <table><thead><tr><th>Shipment</th><th>SME</th><th>Product</th><th>Route</th><th>Breach %</th><th>Max Temp</th><th>Severity</th><th>Recommended Action</th></tr></thead>
  <tbody>${topAlerts}</tbody></table>

  <h2>Product Mix Monitored</h2>
  <table><thead><tr><th>Product</th><th>Shipments</th></tr></thead><tbody>${productRows}</tbody></table>

  <h2>Full Shipment Monitoring Register</h2>
  <table><thead><tr><th>Shipment</th><th>SME</th><th>Product</th><th>Route</th><th>Breach %</th><th>Max Temp (&deg;C)</th><th>Excursion (min)</th><th>Status</th></tr></thead>
  <tbody>${registerRows}</tbody></table>

  <div class="disclaimer"><b>Note:</b> this report is generated from synthetic demo data created for interview purposes, following the same monitoring, alerting, and reporting workflow described for the TRACE Research Associate role. It isn't real PEACEPLUS or SEUPB pilot data.</div>
  <div class="footer">TRACE candidate demo. Auto-generated report. Open this file and use your browser's Print option to save it as a PDF if you need one.</div>
</body></html>`;
  }

  window.__downloadReport = function(){
    const html = buildReportHTML();
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const stamp = new Date().toISOString().slice(0,10);
    a.href = url;
    a.download = `TRACE_Monitoring_Report_${stamp}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
})();
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA_JSON__", DATA_JSON).replace("__HSI_JSON__", HSI_JSON)
OUT_PATH.write_text(HTML, encoding="utf-8")
print("Wrote", OUT_PATH, len(HTML), "bytes")
