"""
TRACE Demo - Synthetic Data Generator
--------------------------------------
Simulates IoT + hyperspectral imaging data for a Products of Animal Origin (POAO)
cross-border cold-chain (farm/processing -> transport -> retail) across a set of
NI/Ireland SME shipments.

Sensor streams (per shipment, per timestep):
  - temperature (C)          : refrigerated unit reading
  - humidity (%)             : relative humidity in transport unit
  - door_events              : count of door-open events in the interval
  - vibration_g              : accelerometer proxy (handling/shock)
  - spectral bands (8 bins)  : simplified hyperspectral reflectance summary
                                (400-1000nm, 8 bands) used to derive a
                                Freshness Index (FI). FI degrades faster
                                when temperature excursions accumulate.

Anomalies injected:
  - Cold-chain breach: refrigeration drift / door left open -> sustained
    temperature excursion above the compliance threshold.
  - Sensor fault: brief dropout / stuck reading (data-quality anomaly,
    distinct from a genuine spoilage risk).

Output files (./data/):
  - shipments.csv          : one row per shipment (metadata + summary labels)
  - sensor_timeseries.csv  : full time series, all shipments, all sensors
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Scenario configuration
# ---------------------------------------------------------------------------
SMES = [
    {"sme_id": "SME-01", "name": "Glenarm Meats Ltd",        "product": "Beef",    "route": "Ballymena -> Dublin"},
    {"sme_id": "SME-02", "name": "Foyle Dairy Co-op",         "product": "Dairy",   "route": "Derry~Londonderry -> Letterkenny"},
    {"sme_id": "SME-03", "name": "Lough Neagh Poultry",       "product": "Poultry", "route": "Craigavon -> Monaghan"},
    {"sme_id": "SME-04", "name": "Mourne Lamb Producers",     "product": "Lamb",    "route": "Newry -> Dundalk"},
    {"sme_id": "SME-05", "name": "Causeway Coast Seafood",    "product": "Seafood", "route": "Coleraine -> Sligo"},
    {"sme_id": "SME-06", "name": "Erne Valley Dairy",         "product": "Dairy",   "route": "Enniskillen -> Cavan"},
]

# Compliance thresholds per product type (EU/UK POAO cold-chain norms, simplified)
COMPLIANCE_TEMP = {
    "Beef": 4.0, "Dairy": 4.0, "Poultry": 4.0, "Lamb": 4.0, "Seafood": 2.0,
}

N_SHIPMENTS_PER_SME = 7
HOURS = 48
STEP_MIN = 15
STEPS = int(HOURS * 60 / STEP_MIN)
SPECTRAL_BANDS = [430, 480, 530, 580, 630, 680, 780, 900]  # nm, simplified 8-band sensor

rows_ts = []
rows_shipment = []

shipment_counter = 1

for sme in SMES:
    for s in range(N_SHIPMENTS_PER_SME):
        shipment_id = f"SHP-{shipment_counter:04d}"
        shipment_counter += 1
        product = sme["product"]
        threshold = COMPLIANCE_TEMP[product]

        # Baseline conditions
        base_temp = threshold - RNG.uniform(1.2, 2.2)
        base_hum = RNG.uniform(78, 88)

        # Decide scenario for this shipment
        scenario = RNG.choice(
            ["normal", "normal", "normal", "cold_chain_breach", "sensor_fault", "minor_fluctuation"],
            p=[0.42, 0.10, 0.08, 0.20, 0.10, 0.10],
        )

        breach_start = RNG.integers(int(STEPS * 0.2), int(STEPS * 0.7)) if scenario == "cold_chain_breach" else None
        breach_len = RNG.integers(6, 16) if scenario == "cold_chain_breach" else 0  # in steps (1.5-4h)
        fault_start = RNG.integers(int(STEPS * 0.1), int(STEPS * 0.8)) if scenario == "sensor_fault" else None
        fault_len = RNG.integers(2, 5) if scenario == "sensor_fault" else 0

        temps, hums, doors, vibs, freshness = [], [], [], [], []
        fi = 1.0  # Freshness Index starts at 1.0 (fresh)
        cum_excursion_minutes = 0

        for t in range(STEPS):
            temp = base_temp + RNG.normal(0, 0.25)
            hum = base_hum + RNG.normal(0, 1.5)
            door = 1 if RNG.random() < 0.03 else 0
            vib = abs(RNG.normal(0.05, 0.02))

            if scenario == "minor_fluctuation":
                temp += RNG.normal(0, 0.6)

            if scenario == "cold_chain_breach" and breach_start <= t < breach_start + breach_len:
                # refrigeration drift: ramps up then holds high
                progress = (t - breach_start) / max(breach_len, 1)
                temp += 3.0 + 4.5 * min(progress * 2, 1.0)
                door = 1 if RNG.random() < 0.25 else door
                vib += RNG.uniform(0.05, 0.15)

            if scenario == "sensor_fault" and fault_start <= t < fault_start + fault_len:
                # stuck/dropout reading
                temp = temps[-1] if temps else base_temp
                hum = np.nan

            # Freshness Index degrades as a function of time-above-threshold.
            # Small baseline decay models natural product ageing over the
            # 48h journey; excursions above the compliance threshold cause a
            # much sharper, compounding decline (thermal abuse -> spoilage).
            if temp > threshold:
                cum_excursion_minutes += STEP_MIN
            baseline_decay = 0.0003
            excursion_decay = (0.0015 + 0.00004 * cum_excursion_minutes) * max(0, temp - threshold)
            fi = max(0.0, fi - baseline_decay - excursion_decay)

            temps.append(round(temp, 2))
            hums.append(round(hum, 2) if not np.isnan(hum) else np.nan)
            doors.append(door)
            vibs.append(round(vib, 3))
            freshness.append(round(fi, 4))

        # Build 8-band spectral reflectance correlated with freshness index
        # Fresh product: higher reflectance in 630-780nm (protein/water bands); degraded: flatter curve
        for t in range(STEPS):
            f = freshness[t]
            base_curve = np.array([0.18, 0.22, 0.28, 0.35, 0.55, 0.62, 0.58, 0.40])
            degraded_curve = np.array([0.20, 0.24, 0.30, 0.34, 0.38, 0.36, 0.34, 0.30])
            curve = degraded_curve + f * (base_curve - degraded_curve)
            curve = curve + RNG.normal(0, 0.01, size=len(SPECTRAL_BANDS))
            curve = np.clip(curve, 0, 1)

            ts = pd.Timestamp("2026-05-12 06:00:00") + pd.Timedelta(minutes=t * STEP_MIN)
            row = {
                "shipment_id": shipment_id,
                "sme_id": sme["sme_id"],
                "sme_name": sme["name"],
                "product": product,
                "route": sme["route"],
                "timestamp": ts,
                "step": t,
                "temperature_c": temps[t],
                "humidity_pct": hums[t],
                "door_open": doors[t],
                "vibration_g": vibs[t],
                "freshness_index": freshness[t],
                "compliance_threshold_c": threshold,
            }
            for b_i, band in enumerate(SPECTRAL_BANDS):
                row[f"band_{band}nm"] = round(float(curve[b_i]), 4)
            rows_ts.append(row)

        # Shipment-level summary
        temps_arr = np.array(temps)
        excursion_minutes = int(np.sum(temps_arr > threshold) * STEP_MIN)
        max_temp = float(np.max(temps_arr))
        final_fi = freshness[-1]
        n_door_events = int(np.sum(doors))

        if scenario == "cold_chain_breach" and excursion_minutes > 60:
            risk_label = "High"
        elif scenario in ("minor_fluctuation",) or (0 < excursion_minutes <= 60):
            risk_label = "Medium"
        elif scenario == "sensor_fault":
            risk_label = "Data Quality Issue"
        else:
            risk_label = "Low"

        rows_shipment.append({
            "shipment_id": shipment_id,
            "sme_id": sme["sme_id"],
            "sme_name": sme["name"],
            "product": product,
            "route": sme["route"],
            "scenario": scenario,
            "compliance_threshold_c": threshold,
            "max_temperature_c": round(max_temp, 2),
            "excursion_minutes": excursion_minutes,
            "door_events": n_door_events,
            "final_freshness_index": round(final_fi, 4),
            "risk_label": risk_label,
            "duration_hours": HOURS,
        })

df_ts = pd.DataFrame(rows_ts)
df_shipment = pd.DataFrame(rows_shipment)

df_ts.to_csv(OUT / "sensor_timeseries.csv", index=False)
df_shipment.to_csv(OUT / "shipments.csv", index=False)

print(f"Generated {len(df_shipment)} shipments across {len(SMES)} SMEs")
print(f"Time series rows: {len(df_ts):,}")
print(df_shipment["risk_label"].value_counts())
print("Saved to:", OUT)
