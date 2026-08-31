"""
NEXUS-NER | Module A — Synthetic Dataset Generator
===================================================
Generates a realistic synthetic dataset for road disruption prediction.

⚠️  IMPORTANT DISCLAIMER
    All data in this file is SYNTHETIC (computer-generated).
    It is designed to produce statistically plausible patterns for
    prototype development and demonstration purposes only.
    Do NOT present model performance on this data as real-world accuracy.

Dataset size  : 10,000 observations (configurable via N_SAMPLES)
Target column : disruption  (0 = no disruption, 1 = disruption)
Output        : services/ai/data/processed/dataset.csv

Usage
-----
    python services/ai/data/generate_dataset.py
"""

import numpy as np
import pandas as pd
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
N_SAMPLES = 10_000
RANDOM_SEED = 42
OUTPUT_DIR = Path(__file__).parent / "processed"
OUTPUT_FILE = OUTPUT_DIR / "dataset.csv"

# Northeast India road corridors used in the simulation
ROAD_IDS = [
    "NH13_001", "NH13_002", "NH13_003", "NH13_004", "NH13_005",
    "NH13_006", "NH13_007", "NH13_008", "NH13_009", "NH13_010",
    "NH15_001", "NH15_002", "NH15_003", "NH15_004", "NH15_005",
    "NH37_001", "NH37_002", "NH37_003", "NH37_004", "NH37_005",
    "NH27_001", "NH27_002", "NH27_003", "NH27_004", "NH27_005",
    "SH01_001", "SH01_002", "SH02_001", "SH02_002", "SH03_001",
]

# Geographic bounding box: Northeast India
LAT_MIN, LAT_MAX = 24.0, 29.5   # Assam → Arunachal Pradesh
LON_MIN, LON_MAX = 89.7, 97.4


# ---------------------------------------------------------------------------
# Helper generators
# ---------------------------------------------------------------------------

def _rainfall(rng: np.random.Generator, n: int) -> tuple:
    """Generate correlated multi-hour rainfall columns (mm)."""
    # Base rainfall — log-normal so most days are dry, some are extreme
    base = rng.lognormal(mean=2.0, sigma=1.4, size=n).clip(0, 250)
    r1h   = (base * rng.uniform(0.1, 0.3, n)).clip(0, 120)
    r3h   = (base * rng.uniform(0.3, 0.6, n)).clip(0, 210)
    r6h   = (base * rng.uniform(0.5, 0.8, n)).clip(0, 250)
    r24h  = base.clip(0, 300)
    return r1h, r3h, r6h, r24h


def _weather(rng: np.random.Generator, n: int) -> tuple:
    """Temperature (°C) and humidity (%) for Northeast India."""
    temp = rng.normal(loc=22.0, scale=6.0, size=n).clip(5, 40)
    hum  = rng.beta(a=5, b=2, size=n) * 100          # skewed high (humid region)
    return temp, hum


def _traffic(rng: np.random.Generator, n: int) -> tuple:
    """Traffic level [0–1] and average speed (km/h)."""
    traffic_level = rng.beta(a=2, b=3, size=n)        # mostly moderate
    avg_speed = (60 - traffic_level * 40 + rng.normal(0, 5, n)).clip(5, 80)
    return traffic_level, avg_speed


def _road(rng: np.random.Generator, n: int) -> tuple:
    """Road condition [0–1], age (years), maintenance score [0–1]."""
    road_condition    = rng.beta(a=3, b=2, size=n)         # skewed good
    road_age          = rng.uniform(1, 30, n)
    maintenance_score = (1 - road_age / 35 + rng.normal(0, 0.1, n)).clip(0.1, 1.0)
    return road_condition, road_age, maintenance_score


def _terrain(rng: np.random.Generator, n: int) -> tuple:
    """Slope (°), elevation (m), river distance (km)."""
    slope          = rng.exponential(scale=12, size=n).clip(0, 60)
    elevation      = rng.uniform(50, 3500, n)
    river_distance = rng.exponential(scale=3, size=n).clip(0.05, 20)
    return slope, elevation, river_distance


def _historical(rng: np.random.Generator, n: int) -> tuple:
    """Historical incident and disruption counts."""
    hist_incidents    = rng.poisson(lam=3, size=n)
    incident_count_7d  = rng.poisson(lam=1, size=n)
    incident_count_30d = rng.poisson(lam=4, size=n)
    prev_disruptions   = rng.poisson(lam=1.5, size=n)
    return hist_incidents, incident_count_7d, incident_count_30d, prev_disruptions


# ---------------------------------------------------------------------------
# Disruption label generation
# ---------------------------------------------------------------------------

def _compute_disruption_probability(
    r1h, r3h, traffic_level, road_condition,
    slope, river_distance, hist_incidents, maintenance_score
) -> np.ndarray:
    """
    Compute a physics-informed latent risk score that determines
    whether a disruption occurs.  Uses a logistic function so the
    label is binary (0/1) with realistic class balance (~22–28% positive).
    """
    # Each term contributes a risk signal in roughly [0, 1]
    rain_signal   = np.tanh(r1h / 60)                          # heavy rain
    rain3h_signal = np.tanh(r3h / 120)
    road_signal   = 1 - road_condition                         # poor road → high risk
    slope_signal  = np.tanh(slope / 30)                        # steep terrain
    river_signal  = np.exp(-river_distance / 2)                # close to river
    hist_signal   = np.tanh(hist_incidents / 8)
    maint_signal  = 1 - maintenance_score
    traffic_sig   = traffic_signal = traffic_level * 0.3       # minor contribution

    # Weighted linear combination
    risk = (
        0.30 * rain_signal
        + 0.15 * rain3h_signal
        + 0.20 * road_signal
        + 0.12 * slope_signal
        + 0.08 * river_signal
        + 0.08 * hist_signal
        + 0.05 * maint_signal
        + 0.02 * traffic_sig
    )

    # Logistic squeeze → probability
    prob = 1 / (1 + np.exp(-8 * (risk - 0.45)))
    return prob


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_dataset(n: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate the full synthetic dataset and return as a DataFrame."""
    rng = np.random.default_rng(seed)

    # --- Road IDs & coordinates ---
    road_id   = rng.choice(ROAD_IDS, size=n)
    latitude  = rng.uniform(LAT_MIN, LAT_MAX, n).round(6)
    longitude = rng.uniform(LON_MIN, LON_MAX, n).round(6)

    # --- Feature groups ---
    r1h, r3h, r6h, r24h             = _rainfall(rng, n)
    temperature, humidity            = _weather(rng, n)
    traffic_level, average_speed     = _traffic(rng, n)
    road_condition, road_age, maint  = _road(rng, n)
    slope, elevation, river_dist     = _terrain(rng, n)
    hist_inc, inc_7d, inc_30d, prev  = _historical(rng, n)

    # --- Disruption label ---
    prob = _compute_disruption_probability(
        r1h, r3h, traffic_level, road_condition,
        slope, river_dist, hist_inc, maint
    )
    disruption = rng.binomial(1, prob)

    df = pd.DataFrame({
        # Identity
        "road_id"               : road_id,
        "latitude"              : latitude,
        "longitude"             : longitude,
        # Weather
        "rainfall_1h"           : r1h.round(2),
        "rainfall_3h"           : r3h.round(2),
        "rainfall_6h"           : r6h.round(2),
        "rainfall_24h"          : r24h.round(2),
        "temperature"           : temperature.round(1),
        "humidity"              : humidity.round(1),
        # Traffic
        "traffic_level"         : traffic_level.round(4),
        "average_speed"         : average_speed.round(1),
        # Road
        "road_condition"        : road_condition.round(4),
        "road_age"              : road_age.round(1),
        "maintenance_score"     : maint.round(4),
        # Terrain
        "slope"                 : slope.round(2),
        "elevation"             : elevation.round(1),
        "river_distance"        : river_dist.round(3),
        # Historical
        "historical_incidents"  : hist_inc,
        "incident_count_7d"    : inc_7d,
        "incident_count_30d"   : inc_30d,
        "previous_disruptions"  : prev,
        # Target
        "disruption"            : disruption,
    })

    return df


def validate_dataset(df: pd.DataFrame) -> None:
    """Run basic sanity checks on the generated dataset."""
    print("\n📊 Dataset Validation")
    print("=" * 50)
    print(f"  Rows               : {len(df):,}")
    print(f"  Columns            : {len(df.columns)}")
    print(f"  Missing values     : {df.isnull().sum().sum()}")
    print(f"  Disruption rate    : {df['disruption'].mean():.1%}  "
          f"({df['disruption'].sum():,} positive / {len(df):,} total)")
    print(f"  Unique road_ids    : {df['road_id'].nunique()}")

    assert df.isnull().sum().sum() == 0,     "❌  Missing values detected"
    assert 0.10 <= df["disruption"].mean() <= 0.45, \
        f"❌  Unusual class balance: {df['disruption'].mean():.1%}"
    assert df["rainfall_1h"].min() >= 0,     "❌  Negative rainfall detected"
    assert df["road_condition"].between(0, 1).all(), "❌  road_condition out of range"
    assert df["traffic_level"].between(0, 1).all(), "❌  traffic_level out of range"
    print("  ✅  All checks passed")


def save_dataset(df: pd.DataFrame, path: Path = OUTPUT_FILE) -> None:
    """Save the dataset to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    size_kb = path.stat().st_size / 1024
    print(f"\n💾 Saved → {path}  ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🚀 NEXUS-NER | Synthetic Dataset Generator")
    print("=" * 50)
    print(f"   Samples        : {N_SAMPLES:,}")
    print(f"   Random seed    : {RANDOM_SEED}")

    df = generate_dataset()
    validate_dataset(df)
    save_dataset(df)

    print("\n✅ Dataset generation complete.")
    print(f"   ⚠️  This is SYNTHETIC data — for prototype use only.\n")
