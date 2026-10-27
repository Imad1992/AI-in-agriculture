"""
TRACE Demo - Monitoring & Alerting (rule-based, no ML)
-------------------------------------------------------
The TRACE Research Associate role is about *monitoring* pilot technologies
(IoT sensors + hyperspectral imaging) across the POAO cold chain, maintaining
technical/operational documentation, and supporting risk registers and
reporting - not building predictive models. This script reflects that scope:

  1. Downsample raw 15-min sensor readings into 1-hour monitoring windows
     (same cadence a pilot dashboard/report would use).
  2. Apply the compliance thresholds defined per product type (POAO cold-
     chain norms) to flag temperature excursions.
  3. Track the Freshness Index derived from the hyperspectral reflectance
     summary as a simple quality-monitoring signal.
  4. Generate a rule-based alerts feed and a shipment-level risk register,
     exactly the kind of output that would feed the project's risk register,
     quarterly reports, and SME-facing dashboards.

No model training, cross-validation, or predictive scoring - this is a
monitoring and reporting pipeline, in line with the job description.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "dashboard_data"
OUT.mkdir(exist_ok=True)

BANDS = [430, 480, 530, 580, 630, 680, 780, 900]

# ---------------------------------------------------------------------------
# Load raw data
# ---------------------------------------------------------------------------
ts = pd.read_csv(DATA / "sensor_timeseries.csv", parse_dates=["timestamp"])
shipments = pd.read_csv(DATA / "shipments.csv")

# ---------------------------------------------------------------------------
# Downsample: 15-min readings -> 1-hour monitoring windows
# ---------------------------------------------------------------------------
ts["hour_bin"] = ts["step"] // 4

def band_freshness_ratio(row):
    # Simple two-band ratio used as a quality-monitoring indicator
    b630 = row["band_630nm"]
    b900 = row["band_900nm"]
    return (b630 - b900) / (b630 + b900 + 1e-6)

ts["spectral_freshness_ratio"] = ts.apply(band_freshness_ratio, axis=1)

hourly = ts.groupby(["shipment_id", "sme_id", "sme_name", "product", "route", "hour_bin"]).agg(
    temp_mean=("temperature_c", "mean"),
    temp_max=("temperature_c", "max"),
    hum_mean=("humidity_pct", "mean"),
    hum_missing=("humidity_pct", lambda x: x.isna().mean()),
    door_events=("door_open", "sum"),
    vib_mean=("vibration_g", "mean"),
    freshness_mean=("freshness_index", "mean"),
    freshness_min=("freshness_index", "min"),
    spectral_ratio_mean=("spectral_freshness_ratio", "mean"),
    threshold=("compliance_threshold_c", "first"),
).reset_index()

hourly["breach_flag"] = (hourly["temp_mean"] - hourly["threshold"] > 1.0).astype(int)
hourly["sensor_fault_flag"] = (hourly["hum_missing"] > 0.2).astype(int)

# ---------------------------------------------------------------------------
# Shipment-level monitoring summary (rule-based, threshold-driven)
# ---------------------------------------------------------------------------
summary = hourly.groupby("shipment_id").agg(
    sme_id=("sme_id", "first"),
    sme_name=("sme_name", "first"),
    product=("product", "first"),
    route=("route", "first"),
    windows=("breach_flag", "count"),
    breach_windows=("breach_flag", "sum"),
    sensor_fault_windows=("sensor_fault_flag", "sum"),
    max_temp=("temp_max", "max"),
    min_freshness=("freshness_min", "min"),
).reset_index()

summary["breach_pct"] = (summary["breach_windows"] / summary["windows"]).round(3)
summary = summary.merge(
    shipments[["shipment_id", "risk_label", "scenario", "excursion_minutes", "door_events"]],
    on="shipment_id",
)

# Monitoring status derived directly from thresholds (no learned model)
def monitoring_status(row):
    if row["breach_pct"] > 0.30 or row["min_freshness"] < 0.60:
        return "High"
    if row["breach_pct"] > 0.05 or row["min_freshness"] < 0.85:
        return "Medium"
    if row["sensor_fault_windows"] > 0:
        return "Data Quality Issue"
    return "Low"

summary["monitoring_status"] = summary.apply(monitoring_status, axis=1)

# ---------------------------------------------------------------------------
# Alerts feed (rule-based thresholds -> operational actions)
# ---------------------------------------------------------------------------
alerts = []
for _, r in summary.sort_values("breach_pct", ascending=False).iterrows():
    if r["monitoring_status"] == "High":
        severity, action = "Critical", "Reject / quarantine batch, notify SME + FSA/FSAI liaison, log SEUPB incident report."
    elif r["monitoring_status"] == "Medium":
        severity, action = "Warning", "Flag for manual QA check on arrival; review refrigeration unit maintenance log."
    elif r["monitoring_status"] == "Data Quality Issue":
        severity, action = "Info", "Sensor dropout detected - schedule IoT device recalibration."
    else:
        continue
    alerts.append({
        "shipment_id": r["shipment_id"],
        "sme_name": r["sme_name"],
        "product": r["product"],
        "route": r["route"],
        "breach_pct": float(r["breach_pct"]),
        "max_temp": float(r["max_temp"]),
        "min_freshness": float(r["min_freshness"]),
        "severity": severity,
        "recommended_action": action,
    })

# ---------------------------------------------------------------------------
# Example shipment for the detailed monitoring view (highest breach_pct)
# ---------------------------------------------------------------------------
example_id = summary.sort_values("breach_pct", ascending=False).iloc[0]["shipment_id"]
example_ts = ts[ts["shipment_id"] == example_id].copy()
example_series = {
    "shipment_id": example_id,
    "sme_name": example_ts["sme_name"].iloc[0],
    "product": example_ts["product"].iloc[0],
    "threshold": float(example_ts["compliance_threshold_c"].iloc[0]),
    "timestamps": example_ts["timestamp"].dt.strftime("%H:%M").tolist(),
    "temperature": example_ts["temperature_c"].tolist(),
    "humidity": example_ts["humidity_pct"].ffill().tolist(),
    "freshness_index": example_ts["freshness_index"].tolist(),
    "spectral_bands": {f"{b}nm": example_ts[f"band_{b}nm"].tolist() for b in BANDS},
    "band_labels": [f"{b}nm" for b in BANDS],
}
step = 2
for k in ["timestamps", "temperature", "humidity", "freshness_index"]:
    example_series[k] = example_series[k][::step]
for b in example_series["spectral_bands"]:
    example_series["spectral_bands"][b] = example_series["spectral_bands"][b][::step]

# ---------------------------------------------------------------------------
# Fleet-wide hourly compliance trend (for a "monitoring over time" chart)
# ---------------------------------------------------------------------------
fleet_hourly = hourly.groupby("hour_bin").agg(
    compliance_pct=("breach_flag", lambda x: round(100 * (1 - x.mean()), 1)),
    avg_freshness=("freshness_mean", lambda x: round(x.mean(), 3)),
).reset_index()

# ---------------------------------------------------------------------------
# Export everything the dashboard needs
# ---------------------------------------------------------------------------
export = {
    "kpis": {
        "total_shipments": int(len(shipments)),
        "total_smes": int(shipments["sme_id"].nunique()),
        "total_sensor_readings": int(len(ts)),
        "high_status": int((summary["monitoring_status"] == "High").sum()),
        "medium_status": int((summary["monitoring_status"] == "Medium").sum()),
        "low_status": int((summary["monitoring_status"] == "Low").sum()),
        "data_quality_status": int((summary["monitoring_status"] == "Data Quality Issue").sum()),
        "compliance_rate_pct": round(100 * (summary["monitoring_status"] == "Low").mean(), 1),
        "avg_breach_minutes": round(shipments["excursion_minutes"].mean(), 1),
    },
    "shipment_monitoring_table": json.loads(summary.sort_values("breach_pct", ascending=False).to_json(orient="records")),
    "alerts": alerts,
    "product_breakdown": shipments["product"].value_counts().to_dict(),
    "sme_breakdown": shipments.groupby("sme_name").size().to_dict(),
    "breach_pct_by_sme": summary.groupby("sme_name")["breach_pct"].mean().round(3).to_dict(),
    "example_series": example_series,
    "fleet_hourly_trend": {
        "hour": fleet_hourly["hour_bin"].tolist(),
        "compliance_pct": fleet_hourly["compliance_pct"].tolist(),
        "avg_freshness": fleet_hourly["avg_freshness"].tolist(),
    },
}

with open(OUT / "dashboard_data.json", "w") as f:
    json.dump(export, f, indent=2, default=str)

print("=== Monitoring summary ===")
print(summary["monitoring_status"].value_counts())
print("\nKPIs:", json.dumps(export["kpis"], indent=2))
print("\nAlerts generated:", len(alerts))
print("Example shipment for detail view:", example_id)
print("Saved dashboard data to:", OUT / "dashboard_data.json")
