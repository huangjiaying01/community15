from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
OUTPUT_ROOT = BASE_DIR / "outputs"

for p in [DATA_RAW, DATA_PROCESSED, OUTPUT_ROOT]:
    p.mkdir(parents=True, exist_ok=True)

CRS_WGS84 = "EPSG:4326"
CRS_CGCS2000 = "EPSG:4547"

WALK_SPEED = 80
TIME_THRESHOLD = 15
SEARCH_RADIUS = 1200

FACILITY_TYPES = ["education", "medical", "commercial", "transport",
                  "elderly", "park", "sports", "culture"]