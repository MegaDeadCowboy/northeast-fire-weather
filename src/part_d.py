"""Part D: data landscape table, RAWS station density, and numbers behind the data-needs list.

Run from repo root (after Parts A and B):  python -m src.part_d
Pulls two small inputs from MegaDeadCowboy/fire-weather-windows (branch northeast-region),
cached to data/reference/: the FEMS Northeast RAWS station list and the Part C result CSVs.
Writes figures/d_*.csv, figures/c_*.csv (copies of Part C results), figures/d_station_density.png.
"""
import io

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from matplotlib.colors import LogNorm

from src.config import FIGURES, PROCESSED, ROOT, STUDY_STATES

DENSITY_STATES = [s for s in STUDY_STATES if s != "DC"]  # FEMS station query covered the 12 states only
from src.part_a import ALBERS, BLUES, HEX_KM, load_states

REF = ROOT / "data" / "reference"
REF.mkdir(parents=True, exist_ok=True)
FWW_RAW = "https://raw.githubusercontent.com/MegaDeadCowboy/fire-weather-windows/northeast-region/"
FWW_FILES = {
    "ne_raws_stations_fems.csv": "data/raw/fems/ne_stations.csv",
    "c_binding_constraint_region.csv": "results/northeast/binding_constraint_region.csv",
    "c_constraint_failures.csv": "results/northeast/constraint_failures.csv",
    "c_hours_in_window_by_month.csv": "results/northeast/hours_in_window_by_month.csv",
}


def fetch_fww():
    for name, path in FWW_FILES.items():
        dest = REF / name
        if not dest.exists():
            local = ROOT.parent / "fire-weather-windows" / path
            if local.exists():
                dest.write_bytes(local.read_bytes())
            else:
                r = requests.get(FWW_RAW + path, timeout=60)
                r.raise_for_status()
                dest.write_bytes(r.content)
        if name.startswith("c_"):
            (FIGURES / name).write_bytes(dest.read_bytes())


def station_density(fires, states):
    st = pd.read_csv(REF / "ne_raws_stations_fems.csv")
    st = st[st["state"].isin(DENSITY_STATES)]
    area_km2 = (states.set_index("STUSPS")["ALAND"] / 1e6 if "ALAND" in states
                else states.set_index("STUSPS").geometry.area / 1e6)
    n_years = fires["FIRE_YEAR"].nunique()
    big = fires[fires["FIRE_SIZE"] >= 10]
    d = pd.DataFrame({
        "raws_stations": st.groupby("state").size(),
        "land_area_km2": area_km2,
        "fires_per_year": fires.groupby("STATE").size() / n_years,
        "fires_ge10ac_per_year": big.groupby("STATE").size() / n_years,
    }).reindex(DENSITY_STATES).fillna({"raws_stations": 0})
    d["stations_per_10k_km2"] = d["raws_stations"] / d["land_area_km2"] * 1e4
    d["fires_ge10ac_per_year_per_station"] = np.where(
        d["raws_stations"] > 0, d["fires_ge10ac_per_year"] / d["raws_stations"], np.nan)
    d.index.name = "state"
    d.round(3).to_csv(FIGURES / "d_station_density_by_state.csv")
    return d, st


def fig_density(fires, st, states):
    pts = gpd.GeoDataFrame(fires, geometry=gpd.points_from_xy(fires["LONGITUDE"], fires["LATITUDE"]),
                           crs="EPSG:4326").to_crs(ALBERS)
    sp = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st["longitude"], st["latitude"]),
                          crs="EPSG:4326").to_crs(ALBERS)
    minx, miny, maxx, maxy = states.total_bounds
    nx = int((maxx - minx) / (HEX_KM * 1000))
    ny = int((maxy - miny) / (HEX_KM * 1000) / np.sqrt(3))
    fig, ax = plt.subplots(figsize=(7, 7))
    hb = ax.hexbin(pts.geometry.x, pts.geometry.y, gridsize=(nx, ny), extent=(minx, maxx, miny, maxy),
                   cmap=BLUES, norm=LogNorm(), mincnt=1, linewidths=0, alpha=0.85)
    states.boundary.plot(ax=ax, color="#666666", linewidth=0.5)
    ax.scatter(sp.geometry.x, sp.geometry.y, s=36, marker="^", facecolor="#ffffff",
               edgecolor="#111111", linewidth=1.2, zorder=5, label=f"RAWS station (FEMS, n={len(sp)})")
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.set_axis_off()
    cb = fig.colorbar(hb, ax=ax, shrink=0.5, pad=0.01)
    cb.set_label(f"Fires per ~{HEX_KM} km hex, 1992–2024 (log scale)")
    ax.set_title("RAWS weather stations vs. wildfire density, Northeast", loc="left", fontsize=10)
    fig.savefig(FIGURES / "d_station_density.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def data_needs_numbers(fires, dens):
    gap = pd.read_csv(FIGURES / "a_mtbs_gap.csv", index_col=0)["value"]
    annual = pd.read_csv(FIGURES / "a_annual_by_state.csv", index_col=0)
    b = pd.read_csv(FIGURES / "b_summary.csv")
    c = pd.read_csv(FIGURES / "c_binding_constraint_region.csv", index_col=0)
    b_all = b[(b["group"] == "all") & (b["variable"] == "erc")].iloc[0]
    rows = [
        ("share_fires_lt500ac_not_mapped_by_mtbs", gap["share_fires_lt500ac"], "a_mtbs_gap.csv"),
        ("share_acres_in_fires_lt500ac", gap["share_acres_lt500ac"], "a_mtbs_gap.csv"),
        ("states_with_zero_raws", int((dens["raws_stations"] == 0).sum()), "d_station_density_by_state.csv"),
        ("raws_stations_total", int(dens["raws_stations"].sum()), "d_station_density_by_state.csv"),
        ("min_stations_per_10k_km2_nonzero", dens.loc[dens["raws_stations"] > 0, "stations_per_10k_km2"].min(),
         "d_station_density_by_state.csv"),
        ("max_stations_per_10k_km2", dens["stations_per_10k_km2"].max(), "d_station_density_by_state.csv"),
        ("ny_fires_per_year_min_1992_2024", annual["NY"].min(), "a_annual_by_state.csv"),
        ("ny_fires_per_year_max_1992_2024", annual["NY"].max(), "a_annual_by_state.csv"),
        ("de_fires_per_year_max_1992_2024", annual["DE"].max(), "a_annual_by_state.csv"),
        ("erc_median_percentile_fires_ge10ac", b_all["median_percentile"], "b_summary.csv"),
        ("share_fires_ge10ac_above_erc_median", b_all["share_drier_than_median"], "b_summary.csv"),
        ("pct_hours_burn_window_open_6_stations", c.loc["ALL_window_open", "pct_complete_hours_failing"],
         "c_binding_constraint_region.csv"),
        ("pct_hours_wind_sole_failure", c.loc["wind", "pct_complete_hours_sole_failure"],
         "c_binding_constraint_region.csv"),
    ]
    pd.DataFrame(rows, columns=["metric", "value", "source_csv"]).to_csv(
        FIGURES / "d_data_needs_numbers.csv", index=False)


def landscape_table(dens):
    n_st = int(dens["raws_stations"].sum())
    zero = ", ".join(dens.index[dens["raws_stations"] == 0])
    gap = pd.read_csv(FIGURES / "a_mtbs_gap.csv", index_col=0)["value"]
    rows = [
        {"dataset": "FPA FOD 7th ed.", "measures": "One point per reported wildfire: discovery date, final size, cause, location",
         "resolution": "Point; location at least as precise as a PLSS section (~2.6 km²)",
         "coverage_latency": "1992–2024; published 2026 (~1.5 yr after last fire year)",
         "northeast_limitations": "Counts follow state reporting systems, not fire activity (see a_annual_by_state.csv); ends 2024",
         "serves": "Fire occurrence research, FPA planning, risk modeling",
         "source": "Short 2026, doi:10.2737/RDS-2013-0009.7; Short 2014 ESSD"},
        {"dataset": "State fire reporting systems (inputs to FPA FOD)", "measures": "Fires responded to by state forestry agencies",
         "resolution": "Point or town/section, varies by state", "coverage_latency": "Varies by state; reaches FPA FOD with the next edition",
         "northeast_limitations": "Reporting starts and stops by state; DE reports 0–39 fires/yr across 1992–2024",
         "serves": "State fire agencies, NASF, FPA FOD compilers",
         "source": "figures/a_annual_by_state.csv; FPA FOD SOURCE_SYSTEM fields"},
        {"dataset": "gridMET", "measures": "Daily surface weather and NFDRS fire-danger indices (ERC, BI, FM100, FM1000)",
         "resolution": "~4 km (1/24°) grid", "coverage_latency": "1979–present, CONUS, updated daily; recent days provisional",
         "northeast_limitations": "One value per 4 km cell vs. point fires; ERC is computed for a single NFDRS fuel model (G) everywhere",
         "serves": "Researchers, drought and fire-danger monitoring",
         "source": "Abatzoglou 2013, Int. J. Climatol. 33:121–131; climatologylab.org/gridmet"},
        {"dataset": "RAWS (via USFS FEMS)", "measures": "Hourly temperature, RH, wind, precipitation, solar radiation, with QC flags",
         "resolution": "Station point", "coverage_latency": "Hourly, near real-time; full period of record in FEMS",
         "northeast_limitations": f"{n_st} active stations across 12 states; none in {zero}",
         "serves": "Fire managers (NFDRS, burn planning), fire-weather forecasters",
         "source": "FEMS Climatology API External User Guide (2025); data/reference/ne_raws_stations_fems.csv"},
        {"dataset": "MTBS", "measures": "Burn perimeters and burn severity for large fires",
         "resolution": "30 m (Landsat; Sentinel-2 resampled to 30 m)", "coverage_latency": "1984–present; typically released 6–12 months after the fire, quarterly releases",
         "northeast_limitations": (f"Maps only fires ≥500 ac in the East; {gap['share_fires_lt500ac']:.1%} of NE fires "
                                   f"({gap['share_acres_lt500ac']:.1%} of NE acres) fall below that"),
         "serves": "Fire effects research, LANDFIRE, land managers",
         "source": "mtbs.gov (project overview, data availability); USGS EROS MTBS page"},
        {"dataset": "NASA FIRMS (MODIS, VIIRS)", "measures": "Satellite active-fire (thermal anomaly) detections",
         "resolution": "MODIS 1 km; VIIRS 375 m", "coverage_latency": "Near real-time, within 3 h of observation; archive available",
         "northeast_limitations": "Misses fires between overpasses or under cloud, smoke or tree canopy; small, cool fires missed by MODIS",
         "serves": "Incident awareness, alerts, global fire monitoring",
         "source": "FIRMS Fire Alerts notes; NASA Earthdata VIIRS 375 m page"},
    ]
    pd.DataFrame(rows).to_csv(FIGURES / "d_data_landscape.csv", index=False)


def main():
    fetch_fww()
    fires = pd.read_parquet(PROCESSED / "fpa_fod_ne_clean.parquet",
                            columns=["STATE", "FIRE_YEAR", "FIRE_SIZE", "LATITUDE", "LONGITUDE"])
    states = load_states()
    dens, st = station_density(fires, states)
    fig_density(fires, st, states)
    landscape_table(dens)
    data_needs_numbers(fires, dens)
    print(dens[["raws_stations", "stations_per_10k_km2", "fires_ge10ac_per_year",
                "fires_ge10ac_per_year_per_station"]].round(2).to_string())
    print(pd.read_csv(FIGURES / "d_data_needs_numbers.csv").to_string(index=False))
    print(f"outputs -> {FIGURES}")


if __name__ == "__main__":
    main()
