#!/usr/bin/env python3
"""Generate synthetic TRACE shipment summaries and IoT sensor timeseries."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

SMES = [
    {"sme_id": "SME-001", "sme_name": "Antrim Beef Co.", "product": "beef", "route": "Ballymena → Dublin"},
    {"sme_id": "SME-002", "sme_name": "Lagan Valley Dairy", "product": "dairy", "route": "Lisburn → Drogheda"},
    {"sme_id": "SME-003", "sme_name": "Foyle Creamery", "product": "dairy", "route": "Derry → Sligo"},
    {"sme_id": "SME-004", "sme_name": "Armagh Poultry Farm", "product": "poultry", "route": "Armagh → Dundalk"},
    {"sme_id": "SME-005", "sme_name": "Mourne Lamb Producers", "product": "lamb", "route": "Newry → Galway"},
    {"sme_id": "SME-006", "sme_name": "North Coast Seafood", "product": "seafood", "route": "Coleraine → Cork"},
]

BANDS = [430, 500, 560, 620, 680, 740, 820, 900]
THRESHOLD_BY_PRODUCT = {
    "beef": 4.0,
    "dairy": 4.0,
    "poultry": 4.0,
    "lamb": 4.0,
    "seafood": 2.0,
}


def _make_scenarios(rng: random.Random, n_shipments: int) -> List[str]:
    scenarios = (
        ["normal"] * 28
        + ["cold_chain_breach"] * 6
        + ["minor_fluctuation"] * 5
        + ["sensor_fault"] * 3
    )
    if len(scenarios) != n_shipments:
        raise ValueError("Scenario allocation must match shipment count")
    rng.shuffle(scenarios)
    return scenarios


def _simulate_series(
    shipment_id: str,
    product: str,
    scenario: str,
    start_time: datetime,
    rng: random.Random,
) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    threshold = THRESHOLD_BY_PRODUCT[product]
    rows: List[Dict[str, float]] = []
    freshness = 1.0

    breach_start = rng.randint(64, 120)
    breach_len = rng.randint(28, 72)
    fluct_windows = {rng.randint(30, 80), rng.randint(100, 155)}
    sensor_fault_steps = {rng.randint(20, 50), rng.randint(90, 130), rng.randint(150, 180)}

    excursion_count = 0
    door_events = 0
    max_temp = -999.0

    for step in range(48 * 4):
        tstamp = start_time + timedelta(minutes=15 * step)
        temp = threshold - 1.2 + rng.uniform(-0.55, 0.55)

        if scenario == "cold_chain_breach" and breach_start <= step < breach_start + breach_len:
            temp = threshold + rng.uniform(1.9, 4.3)
        elif scenario == "minor_fluctuation" and any(abs(step - fw) <= 2 for fw in fluct_windows):
            temp = threshold + rng.uniform(0.2, 1.1)

        if scenario == "sensor_fault" and step in sensor_fault_steps:
            temp = rng.choice([-18.0, 34.0, 45.0])

        humidity = max(35.0, min(95.0, 68.0 + rng.uniform(-10, 10)))
        door_open = 1 if rng.random() < 0.04 else 0
        vibration = max(0.05, 0.22 + rng.uniform(-0.12, 0.38) + (0.25 if door_open else 0.0))

        if door_open:
            door_events += 1
        if temp > threshold:
            excursion_count += 1

        temp_excess = max(0.0, temp - threshold)
        freshness_loss = 0.00045 + (temp_excess * 0.0032)
        freshness = max(0.0, freshness - freshness_loss)

        band_base = [0.25, 0.29, 0.36, 0.44, 0.50, 0.54, 0.58, 0.62]
        spectral = {
            f"band_{band}nm": max(0.0, min(1.0, base + freshness * 0.18 + rng.uniform(-0.015, 0.015)))
            for band, base in zip(BANDS, band_base)
        }

        max_temp = max(max_temp, temp)
        row: Dict[str, float] = {
            "shipment_id": shipment_id,
            "timestamp": tstamp.isoformat(),
            "step": step,
            "temperature_c": round(temp, 3),
            "humidity_pct": round(humidity, 3),
            "door_open": door_open,
            "vibration_g": round(vibration, 4),
            "freshness_index": round(freshness, 4),
        }
        row.update({k: round(v, 4) for k, v in spectral.items()})
        rows.append(row)

    excursion_minutes = excursion_count * 15
    if scenario == "sensor_fault":
        risk_label = "Data Quality Issue"
    elif excursion_minutes >= 180 or freshness < 0.56:
        risk_label = "High"
    elif excursion_minutes >= 60 or freshness < 0.75:
        risk_label = "Medium"
    else:
        risk_label = "Low"

    summary = {
        "max_temperature_c": round(max_temp, 3),
        "excursion_minutes": excursion_minutes,
        "door_events": door_events,
        "final_freshness_index": round(freshness, 4),
        "risk_label": risk_label,
    }
    return rows, summary


def generate_dataset(output_dir: Path, seed: int = 42) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    shipment_rows: List[Dict[str, object]] = []
    sensor_rows: List[Dict[str, object]] = []
    scenarios = _make_scenarios(rng, 42)
    base_time = datetime(2026, 1, 1, 6, 0, 0)

    for idx in range(42):
        shipment_id = f"SHP-{idx + 1:04d}"
        sme = SMES[idx % len(SMES)]
        scenario = scenarios[idx]
        start_time = base_time + timedelta(hours=idx)

        series, summary = _simulate_series(shipment_id, sme["product"], scenario, start_time, rng)
        sensor_rows.extend(series)

        shipment_rows.append(
            {
                "shipment_id": shipment_id,
                "sme_id": sme["sme_id"],
                "sme_name": sme["sme_name"],
                "product": sme["product"],
                "route": sme["route"],
                "scenario": scenario,
                "compliance_threshold_c": THRESHOLD_BY_PRODUCT[sme["product"]],
                "max_temperature_c": summary["max_temperature_c"],
                "excursion_minutes": summary["excursion_minutes"],
                "door_events": summary["door_events"],
                "final_freshness_index": summary["final_freshness_index"],
                "risk_label": summary["risk_label"],
                "duration_hours": 48,
            }
        )

    shipments_path = output_dir / "shipments.csv"
    sensor_path = output_dir / "sensor_timeseries.csv"

    shipment_fields = [
        "shipment_id",
        "sme_id",
        "sme_name",
        "product",
        "route",
        "scenario",
        "compliance_threshold_c",
        "max_temperature_c",
        "excursion_minutes",
        "door_events",
        "final_freshness_index",
        "risk_label",
        "duration_hours",
    ]
    sensor_fields = [
        "shipment_id",
        "timestamp",
        "step",
        "temperature_c",
        "humidity_pct",
        "door_open",
        "vibration_g",
        "freshness_index",
    ] + [f"band_{b}nm" for b in BANDS]

    with shipments_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=shipment_fields)
        writer.writeheader()
        writer.writerows(shipment_rows)

    with sensor_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sensor_fields)
        writer.writeheader()
        writer.writerows(sensor_rows)

    return shipments_path, sensor_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic TRACE shipment and sensor data.")
    parser.add_argument("--output-dir", default="data", help="Directory where CSV files will be written")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    shipments_path, sensor_path = generate_dataset(Path(args.output_dir), args.seed)
    print(f"Wrote {shipments_path}")
    print(f"Wrote {sensor_path}")


if __name__ == "__main__":
    main()
