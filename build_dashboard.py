#!/usr/bin/env python3
"""Build dashboard_data.json and a self-contained TRACE demo dashboard HTML."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List


def _load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _line_points(values: List[float], width: int, height: int, pad: int = 20) -> str:
    if not values:
        return ""
    vmin = min(values)
    vmax = max(values)
    span = (vmax - vmin) or 1.0
    step_x = (width - (2 * pad)) / max(1, (len(values) - 1))
    points = []
    for i, val in enumerate(values):
        x = pad + (i * step_x)
        y = height - pad - ((val - vmin) / span) * (height - (2 * pad))
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def build_dashboard(
    shipments_path: Path,
    sensor_path: Path,
    monitoring_path: Path,
    hyperspectral_path: Path,
    data_output: Path,
    html_output: Path,
) -> None:
    shipments = _load_csv(shipments_path)
    sensors = _load_csv(sensor_path)
    monitoring = _load_json(monitoring_path)
    hyperspectral = _load_json(hyperspectral_path)

    monitored_status = {sid: data["risk_label"] for sid, data in monitoring["shipments"].items()}

    for shipment in shipments:
        shipment["risk_label"] = monitored_status.get(shipment["shipment_id"], shipment["risk_label"])

    by_product = Counter(s["product"] for s in shipments)
    by_status = Counter(s["risk_label"] for s in shipments)

    sme_group = defaultdict(list)
    for s in shipments:
        sme_group[s["sme_name"]].append(float(s["excursion_minutes"]) > 0)
    breach_by_sme = [
        {
            "sme_name": sme,
            "breach_percent": round((sum(vals) / len(vals)) * 100, 2),
            "shipments": len(vals),
        }
        for sme, vals in sme_group.items()
    ]

    selected_id = next((s["shipment_id"] for s in shipments if s["risk_label"] == "High"), shipments[0]["shipment_id"])
    selected_rows = [r for r in sensors if r["shipment_id"] == selected_id]

    temp_series = [float(r["temperature_c"]) for r in selected_rows]
    fresh_series = [float(r["freshness_index"]) for r in selected_rows]
    threshold = next(float(s["compliance_threshold_c"]) for s in shipments if s["shipment_id"] == selected_id)

    band_columns = [c for c in selected_rows[0].keys() if c.startswith("band_")]
    spectral_trend = {band: [float(r[band]) for r in selected_rows] for band in band_columns}

    dashboard_data = {
        "kpis": {
            "total_shipments": len(shipments),
            "total_smes": len({s["sme_id"] for s in shipments}),
            "compliance_rate_pct": round((by_status.get("Low", 0) / len(shipments)) * 100, 2),
            "high_status_count": by_status.get("High", 0),
            "active_alerts": len(monitoring["alerts"]),
        },
        "pipeline_steps": [
            "1) Sensor capture",
            "2) Data generation",
            "3) Rule-based monitoring",
            "4) Alerts and reporting",
            "5) Dashboard visualisation",
        ],
        "alerts": monitoring["alerts"],
        "shipments": shipments,
        "status_breakdown": by_status,
        "product_breakdown": by_product,
        "breach_by_sme": sorted(breach_by_sme, key=lambda r: r["breach_percent"], reverse=True),
        "fleet_trend": monitoring["fleet_trend"],
        "temperature_freshness": {
            "shipment_id": selected_id,
            "timestamps": [r["timestamp"] for r in selected_rows],
            "temperature_c": temp_series,
            "freshness_index": fresh_series,
            "threshold_c": threshold,
        },
        "spectral_trend": {
            "shipment_id": selected_id,
            "timestamps": [r["timestamp"] for r in selected_rows],
            "bands": spectral_trend,
        },
    }

    data_output.parent.mkdir(parents=True, exist_ok=True)
    with data_output.open("w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)

    width, height = 860, 250
    temp_points = _line_points(temp_series, width, height)
    fresh_points = _line_points(fresh_series, width, height)
    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>TRACE Demo Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f3f6f9; color: #1d2733; }}
    header {{ background: #0f4c81; color: white; padding: 16px 20px; }}
    .wrap {{ padding: 16px 20px 28px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: 10px; margin-bottom: 14px; }}
    .card {{ background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 2px rgba(0,0,0,.08); }}
    .banner {{ background: #fff8e1; border-left: 4px solid #f7b500; padding: 10px 12px; margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 6px; text-align: left; }}
    th {{ background: #f0f4f8; }}
    .grid2 {{ display:grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .small {{ font-size: 12px; color:#4a5568; }}
    canvas {{ border:1px solid #d9e2ec; image-rendering: pixelated; width: 300px; height: 300px; }}
    .alerts li {{ margin-bottom: 6px; }}
  </style>
</head>
<body>
<header>
  <h1>TRACE Demo Dashboard (Synthetic Data)</h1>
  <div class=\"small\">This demo is synthetic and for methodology demonstration only; it is not real TRACE pilot data.</div>
</header>
<div class=\"wrap\">
  <section class=\"kpis\" id=\"kpis\"></section>
  <section class=\"banner\"><strong>Pipeline:</strong> <span id=\"pipeline\"></span></section>

  <section class=\"card\">
    <h3>Temperature & Freshness Index (selected shipment)</h3>
    <svg width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\" role=\"img\" aria-label=\"Temperature and Freshness trend\">
      <polyline fill=\"none\" stroke=\"#d9534f\" stroke-width=\"2\" points=\"{temp_points}\"></polyline>
      <polyline fill=\"none\" stroke=\"#2f855a\" stroke-width=\"2\" points=\"{fresh_points}\"></polyline>
    </svg>
    <div class=\"small\">Red = temperature. Green = freshness index.</div>
  </section>

  <section class=\"grid2\" style=\"margin-top:10px;\">
    <div class=\"card\"><h3>Product Breakdown</h3><div id=\"products\"></div></div>
    <div class=\"card\"><h3>Monitoring Status Breakdown</h3><div id=\"statuses\"></div></div>
  </section>

  <section class=\"grid2\" style=\"margin-top:10px;\">
    <div class=\"card\"><h3>Breach % by SME</h3><div id=\"sme\"></div></div>
    <div class=\"card\"><h3>Alerts Feed</h3><ul id=\"alerts\" class=\"alerts\"></ul></div>
  </section>

  <section class=\"card\" style=\"margin-top:10px;\">
    <h3>Hyperspectral Imaging Viewer</h3>
    <label>Shipment: <select id=\"imgShipment\"></select></label>
    <label>Checkpoint: <select id=\"imgCheckpoint\"></select></label>
    <div class=\"grid2\" style=\"margin-top:8px;\">
      <canvas id=\"heatmap\" width=\"20\" height=\"20\"></canvas>
      <div id=\"imgStats\"></div>
    </div>
  </section>

  <section class=\"card\" style=\"margin-top:10px;\">
    <h3>Shipment Monitoring Register</h3>
    <div style=\"max-height:300px;overflow:auto;\"><table id=\"shipmentsTable\"></table></div>
  </section>
</div>

<script>
const DASHBOARD_DATA = {json.dumps(dashboard_data)};
const HYPER = {json.dumps(hyperspectral)};

(function render() {{
  const kpis = DASHBOARD_DATA.kpis;
  document.getElementById('kpis').innerHTML = [
    ['Shipments', kpis.total_shipments],
    ['SMEs', kpis.total_smes],
    ['Compliance %', kpis.compliance_rate_pct],
    ['High status', kpis.high_status_count],
    ['Active alerts', kpis.active_alerts],
  ].map(([k,v]) => `<div class=\"card\"><div class=\"small\">${{k}}</div><div><strong>${{v}}</strong></div></div>`).join('');

  document.getElementById('pipeline').textContent = DASHBOARD_DATA.pipeline_steps.join(' → ');

  document.getElementById('products').innerHTML = Object.entries(DASHBOARD_DATA.product_breakdown)
    .map(([k,v]) => `<div>${{k}}: <strong>${{v}}</strong></div>`).join('');
  document.getElementById('statuses').innerHTML = Object.entries(DASHBOARD_DATA.status_breakdown)
    .map(([k,v]) => `<div>${{k}}: <strong>${{v}}</strong></div>`).join('');
  document.getElementById('sme').innerHTML = DASHBOARD_DATA.breach_by_sme
    .map(r => `<div>${{r.sme_name}}: <strong>${{r.breach_percent}}%</strong> (${{r.shipments}} shipments)</div>`).join('');

  document.getElementById('alerts').innerHTML = DASHBOARD_DATA.alerts.map(a =>
    `<li><strong>${{a.severity.toUpperCase()}}</strong> - ${{a.shipment_id}} (${{a.sme_name}}): ${{a.recommended_action}}</li>`
  ).join('');

  const table = document.getElementById('shipmentsTable');
  const cols = ['shipment_id','sme_name','product','route','scenario','compliance_threshold_c','max_temperature_c','excursion_minutes','door_events','final_freshness_index','risk_label','duration_hours'];
  table.innerHTML = `<thead><tr>${{cols.map(c => `<th>${{c}}</th>`).join('')}}</tr></thead><tbody>${{DASHBOARD_DATA.shipments.map(s => `<tr>${{cols.map(c => `<td>${{s[c]}}</td>`).join('')}}</tr>`).join('')}}</tbody>`;

  const shipSelect = document.getElementById('imgShipment');
  const cpSelect = document.getElementById('imgCheckpoint');
  HYPER.shipments.forEach((s, idx) => {{
    const o = document.createElement('option');
    o.value = idx;
    o.textContent = `${{s.shipment_id}} (${{s.risk_label}})`;
    shipSelect.appendChild(o);
  }});

  function populateCheckpoints() {{
    cpSelect.innerHTML = '';
    const ship = HYPER.shipments[Number(shipSelect.value) || 0];
    ship.checkpoints.forEach((cp, idx) => {{
      const o = document.createElement('option');
      o.value = idx;
      o.textContent = cp.checkpoint;
      cpSelect.appendChild(o);
    }});
  }}

  function renderImage() {{
    const ship = HYPER.shipments[Number(shipSelect.value) || 0];
    const cp = ship.checkpoints[Number(cpSelect.value) || 0];
    const canvas = document.getElementById('heatmap');
    const ctx = canvas.getContext('2d');
    for (let r = 0; r < 20; r++) {{
      for (let c = 0; c < 20; c++) {{
        const q = cp.quality_index_grid[r][c];
        const red = Math.floor((1 - q) * 255);
        const green = Math.floor(q * 200);
        ctx.fillStyle = `rgb(${{red}},${{green}},80)`;
        ctx.fillRect(c, r, 1, 1);
      }}
    }}
    document.getElementById('imgStats').innerHTML = `
      <div><strong>Shipment:</strong> ${{ship.shipment_id}} (${{ship.risk_label}})</div>
      <div><strong>Checkpoint:</strong> ${{cp.checkpoint}}</div>
      <div><strong>Defect %:</strong> ${{cp.defect_percentage}}</div>
      <div><strong>Mean quality:</strong> ${{cp.mean_quality}}</div>
      <div><strong>Normal spectrum:</strong> ${{cp.spectral_signature.normal.join(', ')}}</div>
      <div><strong>Flagged spectrum:</strong> ${{cp.spectral_signature.flagged.join(', ')}}</div>
    `;
  }}

  shipSelect.addEventListener('change', () => {{ populateCheckpoints(); renderImage(); }});
  cpSelect.addEventListener('change', renderImage);
  populateCheckpoints();
  renderImage();
}})();
</script>
</body>
</html>
"""

    html_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build TRACE dashboard data and HTML output.")
    parser.add_argument("--shipments", default="data/shipments.csv")
    parser.add_argument("--sensor", default="data/sensor_timeseries.csv")
    parser.add_argument("--monitoring", default="data/monitoring_analysis.json")
    parser.add_argument("--hyperspectral", default="data/hyperspectral_images.json")
    parser.add_argument("--dashboard-data", default="data/dashboard_data.json")
    parser.add_argument("--dashboard-html", default="dashboard.html")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_dashboard(
        shipments_path=Path(args.shipments),
        sensor_path=Path(args.sensor),
        monitoring_path=Path(args.monitoring),
        hyperspectral_path=Path(args.hyperspectral),
        data_output=Path(args.dashboard_data),
        html_output=Path(args.dashboard_html),
    )
    print(f"Wrote {args.dashboard_data}")
    print(f"Wrote {args.dashboard_html}")


if __name__ == "__main__":
    main()
