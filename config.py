from pathlib import Path

import geopandas as gpd

try:
    gpd.options.io_engine = "pyogrio"
except Exception:
    pass

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_BOUNDARY = DATA_DIR / "boundary"
DATA_BUILTIN = DATA_DIR / "builtin"
OUTPUT_ROOT = BASE_DIR / "outputs"
OUTPUT_FIG = OUTPUT_ROOT / "figures"
OUTPUT_TAB = OUTPUT_ROOT / "tables"
OUTPUT_MAP = OUTPUT_ROOT / "maps"

ALL_DIRS = [
    DATA_DIR,
    DATA_RAW,
    DATA_PROCESSED,
    DATA_BOUNDARY,
    DATA_BUILTIN,
    OUTPUT_ROOT,
    OUTPUT_FIG,
    OUTPUT_TAB,
    OUTPUT_MAP,
]

for p in ALL_DIRS:
    p.mkdir(parents=True, exist_ok=True)

CRS_WGS84 = "EPSG:4326"
CRS_CGCS2000 = "EPSG:4547"

WALK_SPEED = 80
TIME_THRESHOLD = 15
SEARCH_RADIUS = 1200

FACILITY_TYPES = ["education", "medical", "commercial", "transport",
                  "elderly", "park", "sports", "culture"]