"""
TRACE Demo - Hyperspectral IMAGING Simulation
------------------------------------------------
The previous version of this demo only plotted spectral band values over
time - that's a spectrometer trace, not imaging. Real hyperspectral imaging
has a spatial dimension: a camera captures a pixel grid over the product
surface/pallet, and every pixel carries its own reflectance spectrum. This
script simulates that properly.

Design:
  - 4 inspection checkpoints along the POAO journey, matching how a real
    pilot would deploy fixed/handheld hyperspectral cameras at physical
    hand-off points (not continuously, unlike the IoT sensors):
        1. Farm / Origin dispatch
        2. Processing facility
        3. In-transit spot check
        4. Retail / arrival goods-in

  - At each checkpoint, a GRID_SIZE x GRID_SIZE image is captured. Each
    pixel has an 8-band reflectance spectrum (same bands as the sensor
    demo: 430-900nm) and a derived per-pixel Quality Index (band-ratio,
    NDVI-style - this is the standard hyperspectral technique for
    freshness/spoilage assessment).

  - A simple computer-vision step segments each image into "flagged"
    vs "normal" pixels using a fixed quality threshold (basic thresholding
    / connected-region logic - no ML model, consistent with the pilot
    monitoring scope), and reports defect area %.

  - For shipments with a cold-chain breach, a localised defect patch
    (e.g. surface spoilage near the pallet edge, consistent with a
    thermal abuse event) appears and grows at later checkpoints. Normal
    shipments stay uniform and fresh; sensor-fault shipments get one
    corrupted/dropout checkpoint image (camera fault, not product fault).

Output: dashboard_data/hyperspectral_images.json
  Contains full pixel grids (quality index) for 3 example shipments
  (one High, one Medium, one Low status) across all 4 checkpoints, plus
  the average spectral signature for "normal" vs "flagged" pixel regions
  at each checkpoint - so the dashboard can show both the spatial image
  AND the spectral curves that justify the computer-vision segmentation.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(123)
DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "dashboard_data"
OUT.mkdir(exist_ok=True)

BANDS = [430, 480, 530, 580, 630, 680, 780, 900]
CHECKPOINTS = ["Farm / Origin Dispatch", "Processing Facility", "In-Transit Spot Check", "Retail / Arrival Goods-In"]
GRID_SIZE = 20            # 20x20 pixel hyperspectral image per checkpoint
QUALITY_THRESHOLD = 0.60  # below this -> flagged pixel (computer-vision segmentation rule)

shipments = pd.read_csv(DATA / "shipments.csv")

FRESH_CURVE = np.array([0.18, 0.22, 0.28, 0.35, 0.55, 0.62, 0.58, 0.40])
DEGRADED_CURVE = np.array([0.20, 0.24, 0.30, 0.34, 0.38, 0.36, 0.34, 0.30])


def band_quality_ratio(curve):
    """NDVI-style two-band ratio -> single Quality Index per pixel."""
    b630, b900 = curve[4], curve[7]
    ratio = (b630 - b900) / (b630 + b900 + 1e-6)
    # rescale roughly into [0,1] for a friendlier "quality index"
    return float(np.clip(0.5 + ratio * 1.3, 0, 1))


def make_pixel_curve(quality_level, rng):
    curve = DEGRADED_CURVE + quality_level * (FRESH_CURVE - DEGRADED_CURVE)
    curve = curve + rng.normal(0, 0.01, size=len(BANDS))
    return np.clip(curve, 0, 1)


def generate_checkpoint_image(scenario, checkpoint_idx, excursion_severity, rng, sensor_fault=False):
    """Returns (quality_grid [GRID_SIZE x GRID_SIZE], band_cube [GRID_SIZE x GRID_SIZE x 8])."""
    quality_grid = np.clip(0.94 + rng.normal(0, 0.02, size=(GRID_SIZE, GRID_SIZE)), 0, 1)

    if sensor_fault and checkpoint_idx == 2:
        # camera/sensor dropout at the in-transit checkpoint: noisy garbage frame
        quality_grid = np.clip(rng.uniform(0, 1, size=(GRID_SIZE, GRID_SIZE)), 0, 1)
        band_cube = np.zeros((GRID_SIZE, GRID_SIZE, len(BANDS)))
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                band_cube[i, j] = make_pixel_curve(quality_grid[i, j], rng) * rng.uniform(0.3, 1.0)
        return quality_grid, band_cube, True  # flag frame as corrupted

    if scenario == "cold_chain_breach" and checkpoint_idx >= 1:
        # a defect patch starts near a pallet edge after the processing stage
        # and spreads spatially at later checkpoints, proportional to breach severity
        growth = {1: 0.18, 2: 0.50, 3: 0.90}.get(checkpoint_idx, 0) * excursion_severity
        cy, cx = GRID_SIZE * 0.75, GRID_SIZE * 0.25  # near a corner/edge
        yy, xx = np.mgrid[0:GRID_SIZE, 0:GRID_SIZE]
        dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        radius = growth * GRID_SIZE * 0.6
        patch = np.clip(1 - dist / max(radius, 1e-6), 0, 1) ** 1.2
        degrade_amount = patch * (0.35 + 0.65 * excursion_severity)
        quality_grid = np.clip(quality_grid - degrade_amount, 0, 1)

    if scenario == "minor_fluctuation":
        quality_grid = np.clip(quality_grid - rng.normal(0.05, 0.02, size=(GRID_SIZE, GRID_SIZE)), 0, 1)

    band_cube = np.zeros((GRID_SIZE, GRID_SIZE, len(BANDS)))
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            band_cube[i, j] = make_pixel_curve(quality_grid[i, j], rng)

    return quality_grid, band_cube, False


def summarize_checkpoint(quality_grid, band_cube, corrupted):
    flagged_mask = quality_grid < QUALITY_THRESHOLD
    defect_pct = float(100 * flagged_mask.mean())
    mean_quality = float(quality_grid.mean())

    if flagged_mask.any():
        flagged_signature = band_cube[flagged_mask].mean(axis=0).tolist()
    else:
        flagged_signature = [None] * len(BANDS)
    normal_signature = band_cube[~flagged_mask].mean(axis=0).tolist() if (~flagged_mask).any() else [None] * len(BANDS)

    return {
        "defect_pct": round(defect_pct, 1),
        "mean_quality": round(mean_quality, 3),
        "normal_signature": [round(v, 4) if v is not None else None for v in normal_signature],
        "flagged_signature": [round(v, 4) if v is not None else None for v in flagged_signature],
        "corrupted_frame": corrupted,
        "quality_grid": np.round(quality_grid, 3).tolist(),
    }


# ---------------------------------------------------------------------------
# Pick 3 representative shipments: High risk, Medium, Low (compliant)
# ---------------------------------------------------------------------------
high_ship = shipments[shipments["risk_label"] == "High"].sort_values("excursion_minutes", ascending=False).iloc[0]
med_ship = shipments[shipments["risk_label"] == "Medium"].iloc[0]
low_ship = shipments[shipments["risk_label"] == "Low"].iloc[0]
fault_ship = shipments[shipments["risk_label"] == "Data Quality Issue"].iloc[0]

example_shipments = {
    "high": high_ship,
    "medium": med_ship,
    "low": low_ship,
    "sensor_fault": fault_ship,
}

result = {"checkpoints": CHECKPOINTS, "bands": BANDS, "grid_size": GRID_SIZE, "quality_threshold": QUALITY_THRESHOLD, "shipments": {}}

for key, ship in example_shipments.items():
    scenario = ship["scenario"]
    excursion_min = ship["excursion_minutes"]
    severity = float(np.clip(excursion_min / 240.0, 0.2, 1.0)) if excursion_min > 0 else 0.0
    is_fault = scenario == "sensor_fault"

    checkpoint_data = []
    for cp_idx in range(len(CHECKPOINTS)):
        qgrid, bcube, corrupted = generate_checkpoint_image(
            scenario, cp_idx, severity, RNG, sensor_fault=is_fault
        )
        checkpoint_data.append(summarize_checkpoint(qgrid, bcube, corrupted))

    result["shipments"][key] = {
        "shipment_id": ship["shipment_id"],
        "sme_name": ship["sme_name"],
        "product": ship["product"],
        "scenario": scenario,
        "risk_label": ship["risk_label"],
        "checkpoints": checkpoint_data,
    }

with open(OUT / "hyperspectral_images.json", "w") as f:
    json.dump(result, f)

print("Generated hyperspectral imaging data for:")
for key, ship in example_shipments.items():
    print(f"  {key}: {ship['shipment_id']} ({ship['scenario']}, {ship['risk_label']})")
    for cp_name, cp in zip(CHECKPOINTS, result["shipments"][key]["checkpoints"]):
        print(f"    {cp_name}: defect_pct={cp['defect_pct']}% mean_quality={cp['mean_quality']} corrupted={cp['corrupted_frame']}")

print("\nSaved to:", OUT / "hyperspectral_images.json")
