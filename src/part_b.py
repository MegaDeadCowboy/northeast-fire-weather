"""Part B: gridMET ERC and FM100 on each fire's discovery date vs. that cell's own climatology.

Run from repo root (after `python -m src.gridmet`):  python -m src.part_b

Method (decision log #11-#12):
- Fires >= 10 acres from the cleaned FPA FOD Northeast file.
- Value = gridMET cell containing the fire point (nearest cell centre), on the discovery date.
- Percentile = share of that cell's values in the climatology years (1992-2020), within
  +/- 15 days of the discovery day-of-year, that fall below the fire-day value (ties count half).
  High ERC percentile = drier/more energy than normal; LOW FM100 percentile = drier than normal.
Writes figures/b_*.csv and figures/b_erc_percentile_by_month.png.
"""
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from scipy.stats import binomtest

from src.config import FIGURES, PROCESSED
from src.gridmet import OUT as GRID_DIR, coord_names

MIN_ACRES = 10
CLIMO_YEARS = range(1992, 2021)
HALF_WINDOW = 15
SEASONS = {3: "spring", 4: "spring", 5: "spring", 6: "summer_fall", 7: "summer_fall",
           8: "summer_fall", 9: "summer_fall", 10: "summer_fall", 11: "summer_fall",
           12: "winter", 1: "winter", 2: "winter"}


def load_fires():
    df = pd.read_parquet(PROCESSED / "fpa_fod_ne_clean.parquet",
                         columns=["FOD_ID", "STATE", "FIRE_YEAR", "DISCOVERY_DATE", "FIRE_SIZE",
                                  "LATITUDE", "LONGITUDE"])
    df = df[df["FIRE_SIZE"] >= MIN_ACRES].copy()
    df["DISCOVERY_DATE"] = pd.to_datetime(df["DISCOVERY_DATE"]).dt.normalize()
    df["month"] = df["DISCOVERY_DATE"].dt.month
    df["season"] = df["month"].map(SEASONS)
    return df.reset_index(drop=True)


def cell_index(fires, ds):
    lat, lon = coord_names(ds)
    la, lo = ds[lat].values, ds[lon].values
    i = np.abs(la[None, :] - fires["LATITUDE"].values[:, None]).argmin(1)
    j = np.abs(lo[None, :] - fires["LONGITUDE"].values[:, None]).argmin(1)
    step = abs(la[1] - la[0])
    inside = (np.abs(la[i] - fires["LATITUDE"].values) <= step) & \
             (np.abs(lo[j] - fires["LONGITUDE"].values) <= step)
    return i, j, inside


def series_by_year(var, cells, years):
    """{year: (dates, array[n_days, n_cells])} for the unique fire cells."""
    out = {}
    ci = xr.DataArray(cells[:, 0], dims="cell")
    cj = xr.DataArray(cells[:, 1], dims="cell")
    for y in years:
        with xr.open_dataset(GRID_DIR / f"ne_{var}_{y}.nc") as ds:
            lat, lon = coord_names(ds)
            da = ds[list(ds.data_vars)[0]]
            tdim = next((d for d in da.dims if d in ("day", "time")),
                        max((d for d in da.dims if d not in (lat, lon)), key=lambda d: da.sizes[d]))
            extra = [d for d in da.dims if d not in (lat, lon, tdim)]
            da = da.isel({d: 0 for d in extra})  # e.g. a size-1 'crs' dim
            vals = da.isel({lat: ci, lon: cj}).transpose(tdim, "cell").values.astype("float32")
            dates = pd.DatetimeIndex(ds[tdim].values).normalize()
        out[y] = (dates, vals)
    return out


def percentiles(var, fires, cells_of_fire, n_cells):
    years = sorted(set(CLIMO_YEARS) | set(fires["FIRE_YEAR"].unique()))
    data = series_by_year(var, cells_of_fire[1], years)
    # climatology stack: for each climo year, values by day-of-year (1..366)
    climo = np.full((len(CLIMO_YEARS), 367, n_cells), np.nan, dtype="float32")
    for k, y in enumerate(CLIMO_YEARS):
        dates, vals = data[y]
        climo[k, dates.dayofyear, :] = vals
    fire_val = np.full(len(fires), np.nan, dtype="float32")
    pct = np.full(len(fires), np.nan, dtype="float32")
    cell = cells_of_fire[0]
    for n, (y, d) in enumerate(zip(fires["FIRE_YEAR"].values, fires["DISCOVERY_DATE"].values)):
        dates, vals = data[y]
        pos = dates.get_indexer([pd.Timestamp(d)])[0]
        if pos < 0:
            continue
        v = vals[pos, cell[n]]
        fire_val[n] = v
        doy = pd.Timestamp(d).dayofyear
        lo, hi = max(1, doy - HALF_WINDOW), min(366, doy + HALF_WINDOW)
        ref = climo[:, lo:hi + 1, cell[n]].ravel()
        ref = ref[~np.isnan(ref)]
        if np.isnan(v) or ref.size == 0:
            continue
        pct[n] = ((ref < v).sum() + 0.5 * (ref == v).sum()) / ref.size * 100
    return fire_val, pct


def summarise(res):
    rows = []
    for group, g in [("all", res)] + list(res.groupby("season")):
        for var, dry_high in [("erc", True), ("fm100", False)]:
            p = g[f"{var}_pct"].dropna()
            k = int((p > 50).sum()) if dry_high else int((p < 50).sum())
            test = binomtest(k, len(p), 0.5, alternative="greater") if len(p) else None
            rows.append({"group": group, "variable": var, "n_fires": len(p),
                         "median_percentile": round(float(p.median()), 1) if len(p) else np.nan,
                         "share_drier_than_median": round(k / len(p), 3) if len(p) else np.nan,
                         "sign_test_p_one_sided": test.pvalue if test else np.nan})
    return pd.DataFrame(rows)


def fig_by_month(res):
    data = [res.loc[res["month"] == m, "erc_pct"].dropna().values for m in range(1, 13)]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.boxplot(data, positions=range(1, 13), widths=0.55, showfliers=False,
               patch_artist=True, boxprops={"facecolor": "#9dc8f7", "edgecolor": "#1b64be"},
               medianprops={"color": "#0e3d7e", "linewidth": 2},
               whiskerprops={"color": "#1b64be"}, capprops={"color": "#1b64be"})
    ax.axhline(50, color="#666666", linewidth=1, linestyle="--")
    ax.text(12.6, 51, "cell's normal (50th)", fontsize=8, color="#444444", ha="right", va="bottom")
    ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    ax.set_ylim(0, 100)
    ax.set_ylabel("ERC percentile on discovery date\n(vs. same cell, ±15 days, 1992–2020)")
    ax.set_xlabel("Discovery month")
    n = [len(d) for d in data]
    ax.set_title(f"Ignition-day fire danger, Northeast fires ≥{MIN_ACRES} ac (n={sum(n):,})",
                 loc="left", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIGURES / "b_erc_percentile_by_month.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    fires = load_fires()
    with xr.open_dataset(GRID_DIR / "ne_erc_2000.nc") as ds:
        i, j, inside = cell_index(fires, ds)
    qa = [("fires_ge_10ac", len(fires)), ("dropped_outside_grid", int((~inside).sum()))]
    fires, i, j = fires[inside].reset_index(drop=True), i[inside], j[inside]
    cells, inv = np.unique(np.stack([i, j], 1), axis=0, return_inverse=True)
    inv = inv.ravel()

    res = fires[["FOD_ID", "STATE", "FIRE_YEAR", "DISCOVERY_DATE", "month", "season", "FIRE_SIZE"]].copy()
    for var in ["erc", "fm100"]:
        res[var], res[f"{var}_pct"] = percentiles(var, fires, (inv, cells), len(cells))
        qa.append((f"no_{var}_value_or_climatology", int(res[f"{var}_pct"].isna().sum())))
    qa.append(("unique_grid_cells", len(cells)))
    pd.DataFrame(qa, columns=["step", "count"]).to_csv(FIGURES / "b_qa_counts.csv", index=False)
    res.to_csv(FIGURES / "b_fire_percentiles.csv", index=False)
    summ = summarise(res)
    summ.to_csv(FIGURES / "b_summary.csv", index=False)
    (res.groupby("STATE")[["erc_pct", "fm100_pct"]].median().round(1)
        .join(res.groupby("STATE").size().rename("n_fires"))
        .to_csv(FIGURES / "b_median_percentile_by_state.csv"))
    fig_by_month(res)

    print(pd.DataFrame(qa, columns=["step", "count"]).to_string(index=False))
    print(res[["erc", "fm100", "erc_pct", "fm100_pct"]].describe().round(1).to_string())
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
