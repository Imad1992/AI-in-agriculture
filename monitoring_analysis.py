#!/usr/bin/env python3
"""Rule-based shipment monitoring and alert generation."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def _load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_monitoring(shipments_path: Path, sensor_path: Path, output_path: Path) -> Path:
    shipments = _load_csv(shipments_path)
    sensors = _load_csv(sensor_path)

    threshold_by_shipment = {s["shipment_id"]: float(s["compliance_threshold_c"]) for s in shipments}

    per_shipment_rows: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in sensors:
        per_shipment_rows[row["shipment_id"]].append(row)

    statuses = {}
    alerts = []

    for shipment in shipments:
        shipment_id = shipment["shipment_id"]
        threshold = threshold_by_shipment[shipment_id]
        rows = sorted(per_shipment_rows[shipment_id], key=lambda r: int(r["step"]))

        invalid_points = 0
        excursion_points = 0
        max_consecutive_exceeded = 0
        current_consecutive = 0

        hourly_windows = []
        for i in range(0, len(rows), 4):
            block = rows[i : i + 4]
            if not block:
                continue
            temps = [float(r["temperature_c"]) for r in block]
            fresh = [float(r["freshness_index"]) for r in block]
            doors = [int(r["door_open"]) for r in block]
            block_time = datetime.fromisoformat(block[0]["timestamp"]).replace(minute=0, second=0, microsecond=0)

            if any(t < -5.0 or t > 30.0 for t in temps):
                invalid_points += sum(1 for t in temps if t < -5.0 or t > 30.0)

            exceeded = sum(1 for t in temps if t > threshold)
            if exceeded:
                current_consecutive += 1
            else:
                max_consecutive_exceeded = max(max_consecutive_exceeded, current_consecutive)
                current_consecutive = 0

            excursion_points += exceeded

            hourly_windows.append(
                {
                    "timestamp": block_time.isoformat(),
                    "mean_temperature_c": round(sum(temps) / len(temps), 3),
                    "max_temperature_c": round(max(temps), 3),
                    "mean_freshness_index": round(sum(fresh) / len(fresh), 4),
                    "door_events": sum(doors),
                }
            )

        max_consecutive_exceeded = max(max_consecutive_exceeded, current_consecutive)
        excursion_minutes = excursion_points * 15

        if invalid_points >= 3:
            status = "Data Quality Issue"
        elif max_consecutive_exceeded >= 4 or excursion_minutes >= 180:
            status = "High"
        elif excursion_minutes >= 60:
            status = "Medium"
        else:
            status = "Low"

        statuses[shipment_id] = {
            "risk_label": status,
            "excursion_minutes": excursion_minutes,
            "invalid_points": invalid_points,
            "max_consecutive_exceeded_hours": max_consecutive_exceeded,
            "hourly_windows": hourly_windows,
        }

        if status != "Low":
            severity = {"Medium": "warning", "High": "critical", "Data Quality Issue": "data"}[status]
            action = {
                "Medium": "Inspect refrigeration unit and review handling log.",
                "High": "Escalate incident, quarantine load, and notify SME QA immediately.",
                "Data Quality Issue": "Validate sensor calibration and replace faulty probe.",
            }[status]
            alerts.append(
                {
                    "shipment_id": shipment_id,
                    "sme_name": shipment["sme_name"],
                    "severity": severity,
                    "status": status,
                    "recommended_action": action,
                }
            )

    fleet_by_hour: Dict[str, Dict[str, float]] = defaultdict(lambda: {"total": 0, "compliant": 0, "fresh_sum": 0.0})
    for row in sensors:
        sid = row["shipment_id"]
        threshold = threshold_by_shipment[sid]
        dt = datetime.fromisoformat(row["timestamp"]).replace(minute=0, second=0, microsecond=0)
        key = dt.isoformat()

        fleet_by_hour[key]["total"] += 1
        if float(row["temperature_c"]) <= threshold:
            fleet_by_hour[key]["compliant"] += 1
        fleet_by_hour[key]["fresh_sum"] += float(row["freshness_index"])

    fleet_trend = []
    for hour in sorted(fleet_by_hour):
        total = fleet_by_hour[hour]["total"]
        compliant = fleet_by_hour[hour]["compliant"]
        fresh_sum = fleet_by_hour[hour]["fresh_sum"]
        fleet_trend.append(
            {
                "timestamp": hour,
                "compliance_rate_pct": round((compliant / total) * 100, 2) if total else 0.0,
                "avg_freshness_index": round(fresh_sum / total, 4) if total else 0.0,
            }
        )

    payload = {
        "shipments": statuses,
        "alerts": sorted(alerts, key=lambda a: (a["severity"], a["shipment_id"])),
        "fleet_trend": fleet_trend,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rule-based monitoring analysis on synthetic sensor data.")
    parser.add_argument("--shipments", default="data/shipments.csv", help="Input shipments CSV")
    parser.add_argument("--sensor", default="data/sensor_timeseries.csv", help="Input sensor CSV")
    parser.add_argument("--output", default="data/monitoring_analysis.json", help="Output monitoring JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = run_monitoring(Path(args.shipments), Path(args.sensor), Path(args.output))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
