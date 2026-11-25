"""Part A: FPA FOD QA and fire-occurrence summaries for the Northeast.

Run from repo root:  python -m src.part_a
Reads data/processed/fpa_fod_ne.parquet (from src.fetch_fpa_fod).
Writes CSVs + PNGs to figures/ (prefix a_) and data/processed/fpa_fod_ne_clean.parquet.
"""
import zipfile

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from matplotlib.colors import LinearSegmentedColormap, LogNorm

from src.config import FIGURES, FPA_FOD_NE, PROCESSED, RAW, STUDY_STATES

CENSUS_URL = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_20m.zip"
CENSUS_ZIP = RAW / "cb_2023_us_state_20m.zip"
ALBERS = "EPSG:5070"  # CONUS Albers equal-area, metres
MTBS_EAST_MIN_ACRES = 500  # MTBS maps East fires >= 500 ac (brief §4; cite mtbs.gov in decision log)
HEX_KM = 10
BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#cce3fd", "#84b9f3", "#338ced", "#1b64be", "#0e3d7e"])
INK = "#333333"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#999999", "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})


def save(df, name):
    df.to_csv(FIGURES / f"a_{name}.csv", index=not isinstance(df.index, pd.RangeIndex))


def load_states():
    if not CENSUS_ZIP.exists():
        r = requests.get(CENSUS_URL, timeout=60)
        r.raise_for_status()
        CENSUS_ZIP.write_bytes(r.content)
    states = gpd.read_file(f"zip://{CENSUS_ZIP}")
    return states[states["STUSPS"].isin(STUDY_STATES)].to_crs(ALBERS)


def qa(df, states):
    rows = [("raw_records", len(df))]
    df = df.drop_duplicates("FOD_ID")
    rows.append(("dropped_duplicate_FOD_ID", rows[0][1] - len(df)))

    missing = df["DISCOVERY_DATE"].isna() | df["LATITUDE"].isna() | df["LONGITUDE"].isna()
    rows.append(("dropped_missing_date_or_coords", int(missing.sum())))
    df = df[~missing].copy()

    # Likely cross-agency duplicates: same day, same ~1 km location, same final size
    key = [df["DISCOVERY_DATE"].dt.date, df["LATITUDE"].round(2),
           df["LONGITUDE"].round(2), df["FIRE_SIZE"]]
    dup = pd.DataFrame({i: k.values for i, k in enumerate(key)}).duplicated(keep="first")
    rows.append(("dropped_likely_duplicate_same_day_1km_size", int(dup.sum())))
    df = df[~dup.values]

    # Point outside its own STATE polygon (flag only; border/water points are common)
    pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["LONGITUDE"], df["LATITUDE"]),
                           crs="EPSG:4326").to_crs(ALBERS)
    joined = gpd.sjoin(pts[["STATE", "geometry"]], states[["STUSPS", "geometry"]],
                       how="left", predicate="within")
    joined = joined[~joined.index.duplicated()]
    df["FLAG_POINT_OUTSIDE_STATE"] = (joined["STUSPS"] != joined["STATE"]).values
    rows.append(("flagged_point_outside_reported_state", int(df["FLAG_POINT_OUTSIDE_STATE"].sum())))
    rows.append(("clean_records", len(df)))
    save(pd.DataFrame(rows, columns=["step", "records"]).set_index("step"), "qa_counts")
    return df, pts.loc[df.index]


def summaries(df):
    n_years = df["FIRE_YEAR"].nunique()
    by_state = df.groupby("STATE").agg(n_fires=("FOD_ID", "size"), acres_burned=("FIRE_SIZE", "sum"))
    by_state["fires_per_year_mean"] = by_state["n_fires"] / n_years
    by_state["share_of_region_fires"] = by_state["n_fires"] / len(df)
    save(by_state.sort_values("n_fires", ascending=False), "fires_by_state")

    save(df.pivot_table(index="FIRE_YEAR", columns="STATE", values="FOD_ID",
                        aggfunc="size", fill_value=0).rename_axis("fire_year"), "annual_by_state")
    save(df.pivot_table(index="STATE", columns="SOURCE_SYSTEM_TYPE", values="FOD_ID",
                        aggfunc="size", fill_value=0), "source_type_by_state")
    save(df.groupby(["STATE", "SOURCE_SYSTEM"]).size().rename("n_fires").to_frame(),
         "source_system_by_state")

    df["MONTH"] = df["DISCOVERY_DATE"].dt.month
    monthly = df.pivot_table(index="STATE", columns="MONTH", values="FOD_ID",
                             aggfunc="size", fill_value=0).reindex(columns=range(1, 13), fill_value=0)
    save(monthly, "monthly_count_by_state")
    monthly_share = monthly.div(monthly.sum(axis=1), axis=0)
    save(monthly_share, "monthly_share_by_state")

    size = df.groupby("FIRE_SIZE_CLASS").agg(n_fires=("FOD_ID", "size"), acres=("FIRE_SIZE", "sum"))
    size["share_fires"] = size["n_fires"] / size["n_fires"].sum()
    size["share_acres"] = size["acres"] / size["acres"].sum()
    save(size, "size_class")

    below = df["FIRE_SIZE"] < MTBS_EAST_MIN_ACRES
    gap = pd.DataFrame({
        "metric": ["n_fires_total", "n_fires_lt500ac", "share_fires_lt500ac",
                   "acres_total", "acres_lt500ac", "share_acres_lt500ac"],
        "value": [len(df), int(below.sum()), below.mean(), df["FIRE_SIZE"].sum(),
                  df.loc[below, "FIRE_SIZE"].sum(),
                  df.loc[below, "FIRE_SIZE"].sum() / df["FIRE_SIZE"].sum()]}).set_index("metric")
    save(gap, "mtbs_gap")

    cause = df.groupby(["NWCG_CAUSE_CLASSIFICATION", "NWCG_GENERAL_CAUSE"]).size().rename("n_fires").to_frame()
    cause["share"] = cause["n_fires"] / len(df)
    save(cause.sort_values("n_fires", ascending=False), "cause")
    return monthly_share, monthly


def fig_seasonality(share, counts):
    order = counts.sum(axis=1).sort_values(ascending=False).index
    region = counts.sum(axis=0)
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(7, 6.5), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 3]})
    ax0.bar(range(12), region.values / region.sum() * 100, color="#2370cd", width=0.7)
    ax0.set_ylabel("Region, % of fires")
    ax0.spines[["top", "right"]].set_visible(False)
    im = ax1.imshow(share.loc[order].values * 100, aspect="auto", cmap=BLUES)
    ax1.set_yticks(range(len(order)), order)
    ax1.set_xticks(range(12), ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax1.set_xlabel("Discovery month")
    cb = fig.colorbar(im, ax=[ax0, ax1], shrink=0.6, pad=0.02)
    cb.set_label("% of the state's fires")
    fig.suptitle("Northeast wildfire seasonality, FPA FOD 1992–2024\n(states ordered by fire count)",
                 x=0.02, ha="left", fontsize=10)
    fig.savefig(FIGURES / "a_seasonality.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_density(pts, states):
    x, y = pts.geometry.x.values, pts.geometry.y.values
    minx, miny, maxx, maxy = states.total_bounds
    fig, ax = plt.subplots(figsize=(7, 7))
    nx = int((maxx - minx) / (HEX_KM * 1000))
    ny = int((maxy - miny) / (HEX_KM * 1000) / np.sqrt(3))  # regular hexagons
    hb = ax.hexbin(x, y, gridsize=(nx, ny),
                   extent=(minx, maxx, miny, maxy), cmap=BLUES, norm=LogNorm(), mincnt=1, linewidths=0)
    states.boundary.plot(ax=ax, color="#666666", linewidth=0.5)
    ax.set_axis_off()
    cb = fig.colorbar(hb, ax=ax, shrink=0.5, pad=0.01)
    cb.set_label(f"Fires per ~{HEX_KM} km hex, 1992–2024 (log scale)")
    ax.set_title("Northeast wildfire density (FPA FOD 7th ed.)", loc="left", fontsize=10)
    fig.savefig(FIGURES / "a_fire_density.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    df = pd.read_parquet(FPA_FOD_NE)
    if "geometry" in df.columns:
        df = df.drop(columns="geometry")
    states = load_states()
    df, pts = qa(df, states)
    df.to_parquet(PROCESSED / "fpa_fod_ne_clean.parquet")
    share, counts = summaries(df)
    fig_seasonality(share, counts)
    fig_density(pts, states)

    qa_t = pd.read_csv(FIGURES / "a_qa_counts.csv", index_col=0)["records"]
    gap = pd.read_csv(FIGURES / "a_mtbs_gap.csv", index_col=0)["value"]
    print(qa_t.to_string())
    print(f"years: {df['FIRE_YEAR'].min()}-{df['FIRE_YEAR'].max()}")
    print(f"share fires <500 ac: {gap['share_fires_lt500ac']:.3f} | "
          f"share acres <500 ac: {gap['share_acres_lt500ac']:.3f}")
    print("source types (NY, DE):")
    print(pd.read_csv(FIGURES / "a_source_type_by_state.csv", index_col=0).loc[["NY", "DE"]].to_string())
    print(f"outputs -> {FIGURES}")


if __name__ == "__main__":
    main()
