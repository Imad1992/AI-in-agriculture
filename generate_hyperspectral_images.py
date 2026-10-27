#!/usr/bin/env python3
"""Generate synthetic hyperspectral checkpoint image data."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Dict, List

BANDS = [430, 500, 560, 620, 680, 740, 820, 900]
CHECKPOINTS = [
    "Farm/Origin Dispatch",
    "Processing Facility",
    "In-Transit Spot Check",
    "Retail/Arrival Goods-In",
]


def _load_shipments(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _pick_examples(shipments: List[Dict[str, str]]) -> List[Dict[str, str]]:
    labels = ["High", "Medium", "Low", "Data Quality Issue"]
    examples: List[Dict[str, str]] = []
    for label in labels:
        match = next((s for s in shipments if s["risk_label"] == label), None)
        if match:
            examples.append(match)
    if len(examples) < 4:
        seen = {s["shipment_id"] for s in examples}
        for shipment in shipments:
            if shipment["shipment_id"] not in seen:
                examples.append(shipment)
                seen.add(shipment["shipment_id"])
            if len(examples) == 4:
                break
    return examples[:4]


def _severity_profile(label: str) -> List[float]:
    if label == "High":
        return [0.06, 0.14, 0.27, 0.39]
    if label == "Medium":
        return [0.03, 0.07, 0.13, 0.19]
    if label == "Data Quality Issue":
        return [0.02, 0.05, 0.06, 0.09]
    return [0.01, 0.02, 0.03, 0.04]


def _make_curve(base_shift: float, rng: random.Random) -> List[float]:
    baseline = [0.28, 0.31, 0.36, 0.42, 0.47, 0.52, 0.57, 0.61]
    return [round(max(0.0, min(1.0, b + base_shift + rng.uniform(-0.01, 0.01))), 4) for b in baseline]


def generate_images(shipments_path: Path, output_path: Path, seed: int = 42) -> Path:
    rng = random.Random(seed + 101)
    shipments = _load_shipments(shipments_path)
    examples = _pick_examples(shipments)

    payload: Dict[str, object] = {
        "metadata": {"bands_nm": BANDS, "checkpoints": CHECKPOINTS, "grid_size": [20, 20]},
        "shipments": [],
    }

    for shipment in examples:
        label = shipment["risk_label"]
        defect_profile = _severity_profile(label)
        shipment_entry: Dict[str, object] = {
            "shipment_id": shipment["shipment_id"],
            "product": shipment["product"],
            "risk_label": label,
            "checkpoints": [],
        }

        for checkpoint_idx, checkpoint_name in enumerate(CHECKPOINTS):
            target_defect_ratio = defect_profile[checkpoint_idx]
            quality_grid: List[List[float]] = []
            flagged_mask: List[List[int]] = []

            defect_size = max(2, int((target_defect_ratio ** 0.5) * 20))
            defect_start_row = max(0, 20 - defect_size)
            defect_start_col = 0

            for r in range(20):
                row_values: List[float] = []
                row_mask: List[int] = []
                for c in range(20):
                    in_defect_patch = r >= defect_start_row and c < defect_size
                    quality = rng.uniform(0.78, 0.93)
                    if in_defect_patch:
                        quality -= rng.uniform(0.20, 0.42)
                    if label == "Data Quality Issue" and rng.random() < 0.02:
                        quality = rng.uniform(0.35, 0.98)
                    quality = max(0.0, min(1.0, quality))
                    flagged = 1 if quality < 0.62 else 0
                    row_values.append(round(quality, 4))
                    row_mask.append(flagged)
                quality_grid.append(row_values)
                flagged_mask.append(row_mask)

            flagged_count = sum(sum(row) for row in flagged_mask)
            defect_percentage = round((flagged_count / 400.0) * 100, 2)
            mean_quality = round(sum(sum(row) for row in quality_grid) / 400.0, 4)

            normal_curve = _make_curve(0.08 - (checkpoint_idx * 0.01), rng)
            flagged_curve = _make_curve(-0.06 - (checkpoint_idx * 0.02), rng)

            shipment_entry["checkpoints"].append(
                {
                    "checkpoint": checkpoint_name,
                    "defect_percentage": defect_percentage,
                    "mean_quality": mean_quality,
                    "quality_index_grid": quality_grid,
                    "flagged_mask": flagged_mask,
                    "spectral_signature": {
                        "normal": normal_curve,
                        "flagged": flagged_curve,
                    },
                }
            )

        payload["shipments"].append(shipment_entry)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic hyperspectral checkpoint images.")
    parser.add_argument("--shipments", default="data/shipments.csv", help="Input shipments CSV")
    parser.add_argument("--output", default="data/hyperspectral_images.json", help="Output JSON path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = generate_images(Path(args.shipments), Path(args.output), seed=args.seed)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
