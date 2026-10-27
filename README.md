# TRACE Demo Dashboard (Synthetic)

This repository contains a small synthetic demo for a TRACE-style POAO cold-chain monitoring workflow.

**Important:** this is not real TRACE project data and not a production TRACE system. It is a transparent technical demonstration of approach.

## What the demo includes

The pipeline is intentionally split into four clear steps:

1. **`generate_data.py`**
   - Generates 42 synthetic shipments across 6 fictional cross-border SMEs.
   - Simulates 48-hour journeys with IoT readings every 15 minutes.
   - Outputs:
     - `data/shipments.csv` (42 rows)
     - `data/sensor_timeseries.csv` (8,064 rows)

2. **`generate_hyperspectral_images.py`**
   - Creates synthetic checkpoint hyperspectral image data for 4 example shipments.
   - 4 checkpoints per shipment; each image is a 20×20 pixel quality-index grid with 8-band spectral signatures.
   - Outputs:
     - `data/hyperspectral_images.json`

3. **`monitoring_analysis.py`**
   - Applies rule-based monitoring logic (no ML/prediction).
   - Downsamples to hourly windows and assigns shipment status:
     - `Low`, `Medium`, `High`, `Data Quality Issue`
   - Generates alerts and fleet compliance/freshness trend.
   - Outputs:
     - `data/monitoring_analysis.json`

4. **`build_dashboard.py`**
   - Builds precomputed dashboard data and a self-contained dashboard page.
   - Outputs:
     - `data/dashboard_data.json`
     - `dashboard.html`

## Data model summary

### `shipments.csv`
One row per shipment with columns:
- `shipment_id`, `sme_id`, `sme_name`, `product`, `route`, `scenario`
- `compliance_threshold_c`, `max_temperature_c`, `excursion_minutes`, `door_events`
- `final_freshness_index`, `risk_label`, `duration_hours`

### `sensor_timeseries.csv`
One row per 15-minute reading with columns:
- `shipment_id`, `timestamp`, `step`
- `temperature_c`, `humidity_pct`, `door_open`, `vibration_g`, `freshness_index`
- `band_430nm` through `band_900nm` (8 spectral point-sensor bands)

### `hyperspectral_images.json`
For each checkpoint image:
- 20×20 `quality_index_grid`
- `defect_percentage`, `mean_quality`
- average `spectral_signature` (`normal` vs `flagged`) over 8 bands

### `dashboard_data.json`
Precomputed dashboard payload including:
- KPIs, alerts, shipment register, product and SME breakdowns, status breakdown, fleet trend
- selected-shipment temperature/freshness and spectral trend series

## Run locally

```bash
python generate_data.py
python generate_hyperspectral_images.py
python monitoring_analysis.py
python build_dashboard.py
```

Then open `dashboard.html` in a browser.
