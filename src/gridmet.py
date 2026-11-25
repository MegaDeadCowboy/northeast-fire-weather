"""Download gridMET yearly netCDF, crop to the Northeast, keep only the crop.

Run from repo root:  python -m src.gridmet            (all vars, 1992-2024)
                     python -m src.gridmet --years 2020 (test one year)

Source: Climatology Lab gridMET (Abatzoglou 2013), direct download
http://www.northwestknowledge.net/metdata/data/<var>_<year>.nc
Each full CONUS file (~75-135 MB) is deleted after cropping; crops go to data/raw/gridmet/.
"""
import argparse

import requests
import xarray as xr

from src.config import RAW

GRIDMET_URL = "http://www.northwestknowledge.net/metdata/data/{var}_{year}.nc"
VARS = ["erc", "fm100"]
YEARS = range(1992, 2025)
# Northeast states bounding box plus margin (deg); WV south edge ~37.2, ME north edge ~47.5
BBOX = {"lat_min": 37.0, "lat_max": 47.6, "lon_min": -82.8, "lon_max": -66.8}
OUT = RAW / "gridmet"
OUT.mkdir(parents=True, exist_ok=True)


def coord_names(ds):
    lat = next(c for c in ds.coords if c.lower().startswith("lat"))
    lon = next(c for c in ds.coords if c.lower().startswith("lon"))
    return lat, lon


def crop(var, year):
    out = OUT / f"ne_{var}_{year}.nc"
    if out.exists():
        return out
    tmp = OUT / f"tmp_{var}_{year}.nc"
    if not tmp.exists():
        with requests.get(GRIDMET_URL.format(var=var, year=year), stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(tmp.with_suffix(".part"), "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        tmp.with_suffix(".part").rename(tmp)
    with xr.open_dataset(tmp) as ds:
        lat, lon = coord_names(ds)
        lat_slice = (slice(BBOX["lat_max"], BBOX["lat_min"]) if ds[lat][0] > ds[lat][-1]
                     else slice(BBOX["lat_min"], BBOX["lat_max"]))
        sub = ds.sel({lat: lat_slice, lon: slice(BBOX["lon_min"], BBOX["lon_max"])}).load()
    enc = {v: {"zlib": True, "complevel": 4} for v in sub.data_vars}
    sub.to_netcdf(out, encoding=enc)
    tmp.unlink()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    ap.add_argument("--vars", nargs="*", default=VARS)
    a = ap.parse_args()
    for var in a.vars:
        for y in a.years:
            p = crop(var, y)
            print(f"{var} {y} -> {p.name} ({p.stat().st_size / 1e6:.1f} MB)", flush=True)
    with xr.open_dataset(p) as ds:
        lat, lon = coord_names(ds)
        dv = list(ds.data_vars)
        print(f"check {p.name}: vars={dv} dims={dict(ds.sizes)} "
              f"lat {float(ds[lat].min()):.2f}-{float(ds[lat].max()):.2f} "
              f"lon {float(ds[lon].min()):.2f}-{float(ds[lon].max()):.2f} "
              f"units={ds[dv[0]].attrs.get('units')}")


if __name__ == "__main__":
    main()
