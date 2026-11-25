"""Build figures/key_results.csv from the part CSVs and write it into README.md between markers.

Run from repo root:  python -m src.results_table
Every value is read from a CSV in figures/; nothing is typed by hand.
"""
import pandas as pd

from src.config import FIGURES, ROOT

F = FIGURES


def build():
    qa = pd.read_csv(F / "a_qa_counts.csv", index_col=0)["records"]
    monthly = pd.read_csv(F / "a_monthly_count_by_state.csv", index_col=0).sum()
    gap = pd.read_csv(F / "a_mtbs_gap.csv", index_col=0)["value"]
    cause = pd.read_csv(F / "a_cause.csv")
    nat = cause.loc[cause["NWCG_CAUSE_CLASSIFICATION"] == "Natural", "share"].sum()
    b = pd.read_csv(F / "b_summary.csv").set_index(["group", "variable"])
    bst = pd.read_csv(F / "b_median_percentile_by_state.csv", index_col=0)
    c = pd.read_csv(F / "c_binding_constraint_region.csv", index_col=0)
    cf = pd.read_csv(F / "c_constraint_failures.csv")
    dens = pd.read_csv(F / "d_station_density_by_state.csv", index_col=0)

    spring = monthly.iloc[2:5].sum() / monthly.sum()
    rows = [
        ("Q1", "Fires in record (cleaned), 1992–2024", f"{int(qa['clean_records']):,}", "a_qa_counts.csv"),
        ("Q1", "Share of fires discovered Mar–May", f"{spring:.1%}", "a_monthly_count_by_state.csv"),
        ("Q1", "Share of fires < 500 ac (below MTBS's eastern threshold)", f"{gap['share_fires_lt500ac']:.1%}", "a_mtbs_gap.csv"),
        ("Q1", "Share of burned area in fires < 500 ac", f"{gap['share_acres_lt500ac']:.1%}", "a_mtbs_gap.csv"),
        ("Q1", "Share of fires with a natural (lightning) cause", f"{nat:.1%}", "a_cause.csv"),
        ("Q2", "Fires ≥ 10 ac scored against their own cell's climatology", f"{int(b.loc[('all', 'erc'), 'n_fires']):,}", "b_summary.csv"),
        ("Q2", "Median ERC percentile on discovery day", f"{b.loc[('all', 'erc'), 'median_percentile']:.1f}", "b_summary.csv"),
        ("Q2", "Share of fires on days above the cell's median ERC", f"{b.loc[('all', 'erc'), 'share_drier_than_median']:.1%}", "b_summary.csv"),
        ("Q2", "Median FM100 percentile on discovery day (low = dry)", f"{b.loc[('all', 'fm100'), 'median_percentile']:.1f}", "b_summary.csv"),
        ("Q2", "Range of state median ERC percentiles", f"{bst['erc_pct'].min():.1f}–{bst['erc_pct'].max():.1f}", "b_median_percentile_by_state.csv"),
        ("Q3", "Hours inside the burn window, 6 RAWS, 2025", f"{c.loc['ALL_window_open', 'pct_complete_hours_failing']:.1f}%", "c_binding_constraint_region.csv"),
        ("Q3", "Hours failing on wind (almost all too calm)", f"{c.loc['wind', 'pct_complete_hours_failing']:.1f}%", "c_binding_constraint_region.csv"),
        ("Q3", "Hours failing on RH (almost all too humid)", f"{c.loc['rh', 'pct_complete_hours_failing']:.1f}%", "c_binding_constraint_region.csv"),
        ("Q3", "Temperature failures that were too hot", f"{int(cf['temp_too_hot_hours'].sum()):,} of {int(cf['temp_fail_hours'].sum()):,} h", "c_constraint_failures.csv"),
        ("Q4", "Active RAWS stations (FEMS), 12 states", f"{int(dens['raws_stations'].sum())}", "d_station_density_by_state.csv"),
        ("Q4", "States with no RAWS station", ", ".join(dens.index[dens["raws_stations"] == 0]), "d_station_density_by_state.csv"),
        ("Q4", "RAWS per 10,000 km² of land, lowest to highest (states with ≥1)",
         f"{dens.loc[dens['raws_stations'] > 0, 'stations_per_10k_km2'].min():.2f}–{dens['stations_per_10k_km2'].max():.2f}",
         "d_station_density_by_state.csv"),
    ]
    df = pd.DataFrame(rows, columns=["question", "result", "value", "source_csv"])
    df.to_csv(F / "key_results.csv", index=False)
    return df


def write_readme(df):
    md = ["| Q | Result | Value | Source |", "|---|---|---|---|"]
    md += [f"| {r.question} | {r.result} | {r.value} | `figures/{r.source_csv}` |" for r in df.itertuples()]
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = "<!-- results:start -->", "<!-- results:end -->"
    block = f"{start}\n" + "\n".join(md) + f"\n{end}"
    if start in text:
        text = text[:text.index(start)] + block + text[text.index(end) + len(end):]
    else:
        text = text.replace("## Key results\n", "## Key results\n\n" + block + "\n", 1)
    readme.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    df = build()
    write_readme(df)
    print(df[["question", "result", "value"]].to_string(index=False))
