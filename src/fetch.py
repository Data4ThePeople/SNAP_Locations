"""Download and cache the USDA historical SNAP retailer archive.

The source is a single static file. FNS was renamed FNA on 2026-06-01 and
fns.usda.gov URLs are being migrated, so the zip is cached in-repo and this
script is a no-op once the CSV exists.
"""
import sys
import zipfile

from config import CSV_PATH, RAW, SOURCE_URL, ZIP_MEMBER, ZIP_PATH


def fetch(force: bool = False) -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    if CSV_PATH.exists() and not force:
        size_mb = CSV_PATH.stat().st_size / 1e6
        print(f"CSV already cached: {CSV_PATH} ({size_mb:.0f} MB) — skipping")
        return

    if not ZIP_PATH.exists() or force:
        import requests

        print(f"Downloading {SOURCE_URL}")
        resp = requests.get(SOURCE_URL, timeout=300, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        ZIP_PATH.write_bytes(resp.content)
        print(f"  wrote {ZIP_PATH} ({len(resp.content) / 1e6:.1f} MB)")

    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = zf.namelist()
        member = ZIP_MEMBER if ZIP_MEMBER in names else names[0]
        print(f"Extracting {member!r}")
        with zf.open(member) as src, open(CSV_PATH, "wb") as dst:
            dst.write(src.read())

    print(f"  wrote {CSV_PATH} ({CSV_PATH.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    fetch(force="--force" in sys.argv)
