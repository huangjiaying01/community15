import os
from pathlib import Path
from config import BASE_DIR

REPO_ID = "XXXCBHDQ/community15-data"
BUILTIN_DIR = BASE_DIR / "data" / "builtin"


def ensure_data():
    BUILTIN_DIR.mkdir(parents=True, exist_ok=True)

    check_file = BUILTIN_DIR / "road_county.shp"
    if check_file.exists():
        print("Data already exists, skip download")
        return

    print("Downloading data from ModelScope...")
    try:
        from modelscope import snapshot_download
        snapshot_download(
            REPO_ID,
            repo_type="dataset",
            cache_dir=str(BUILTIN_DIR),
            local_dir=str(BUILTIN_DIR),
        )
        print("Download complete")
    except Exception as e:
        print(f"Download failed: {e}")