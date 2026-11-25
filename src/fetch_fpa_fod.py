"""Download FPA FOD 7th ed. (cached), inspect schema, filter to study states.

Run from repo root:  python -m src.fetch_fpa_fod
Outputs:
  data/raw/<zip> and extracted .gpkg   (cached, never re-downloaded)
  data/processed/fpa_fod_schema.txt    layers + columns, for verifying field names
  data/processed/fpa_fod_ne.parquet    Northeast subset
"""
import sys
import zipfile

import pyogrio
import requests

from src.config import FPA_FOD_URL, FPA_FOD_ZIP, FPA_FOD_NE, PROCESSED, RAW, STUDY_STATES


def download():
    if FPA_FOD_ZIP.exists():
        print(f"cached: {FPA_FOD_ZIP.name}")
        return
    print("downloading FPA FOD GPKG (~227 MB)...")
    tmp = FPA_FOD_ZIP.with_suffix(".part")
    with requests.get(FPA_FOD_URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.rename(FPA_FOD_ZIP)


def extract():
    existing = list(RAW.rglob("*.gpkg"))
    if existing:
        return existing[0]
    with zipfile.ZipFile(FPA_FOD_ZIP) as z:
        z.extractall(RAW / "fpa_fod_7")
    return next(RAW.rglob("*.gpkg"))


def write_schema(gpkg):
    lines = []
    for name, geom in pyogrio.list_layers(gpkg):
        info = pyogrio.read_info(gpkg, layer=name)
        lines.append(f"## layer={name} geom={geom} n={info['features']}")
        lines += [f"  {c} ({t})" for c, t in zip(info["fields"], info["dtypes"])]
    out = PROCESSED / "fpa_fod_schema.txt"
    out.write_text("\n".join(lines))
    return out


def main():
    download()
    gpkg = extract()
    schema = write_schema(gpkg)
    layers = [l for l, g in pyogrio.list_layers(gpkg) if g]  # spatial layers only
    if len(layers) != 1:
        sys.exit(f"Expected 1 spatial layer, found {layers}. See {schema}")
    layer = layers[0]
    fields = pyogrio.read_info(gpkg, layer=layer)["fields"]
    if "STATE" not in fields:
        sys.exit(f"No STATE field in layer {layer}. See {schema}")

    states = ",".join(f"'{s}'" for s in STUDY_STATES)
    gdf = pyogrio.read_dataframe(gpkg, layer=layer, where=f"STATE IN ({states})")
    gdf.to_parquet(FPA_FOD_NE)

    print(f"gpkg: {gpkg.name} | layer: {layer} | national n: "
          f"{pyogrio.read_info(gpkg, layer=layer)['features']}")
    print(f"NE subset shape: {gdf.shape}")
    print(gdf["STATE"].value_counts().to_string())
    print(f"schema -> {schema}\nsubset -> {FPA_FOD_NE}")


if __name__ == "__main__":
    main()
