"""Shared paths and study-region settings. See docs/decision_log.md #2, #3."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"
for p in (RAW, PROCESSED, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

# Decision log #2: USDA Northeast Climate Hub region
STUDY_STATES = ["CT", "DE", "MD", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT", "WV", "DC"]

# Decision log #3: FPA FOD 7th edition, GeoPackage (doi:10.2737/RDS-2013-0009.7)
FPA_FOD_URL = (
    "https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7/"
    "RDS-2013-0009.7_Data_Format3_GPKG.zip"
)
FPA_FOD_ZIP = RAW / "RDS-2013-0009.7_Data_Format3_GPKG.zip"
FPA_FOD_NE = PROCESSED / "fpa_fod_ne.parquet"
