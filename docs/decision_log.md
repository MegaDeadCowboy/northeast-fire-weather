# Decision Log

Each entry: what was chosen, why, the number behind it, and the source.

| # | Date | Decision | Why | Number | Source |
|---|---|---|---|---|---|
| 1 | 2026-11-25 | New repo `northeast-fire-weather` for Parts A, B, D; Part C goes in fire-weather-windows as `regions/northeast` | Per brief §7 | — | docs/project_brief.md |
| 2 | 2026-11-25 | Study region = CT, DE, MD, ME, MA, NH, NJ, NY, PA, RI, VT, WV + DC | Hub About page gives only "twelve Northeastern States plus DC"; USDA's Northeast Hub page names them | 12 states + DC | climatehubs.usda.gov/hubs/northeast/about; usda.gov/node/19049 |
| 3 | 2026-11-25 | Use FPA FOD **7th edition** (FPA_FOD_20260615, 1992–2024), GeoPackage, not the 6th (1992–2020) in the brief | Brief open question #1: the 7th edition is out; 4 more years of data, same format. Brief text "29 years / ends 2020" becomes 33 years / ends 2024 | 2.66M records nationally; GPKG zip 227.14 MB | Short 2026, doi:10.2737/RDS-2013-0009.7 |
| 4 | 2026-11-25 | Part A QA: drop duplicate FOD_ID; drop missing date or coords; drop likely cross-agency duplicates (same discovery day, lat/lon rounded to 0.01° ≈ 1 km, same FIRE_SIZE), keep first; flag (not drop) points outside their reported STATE polygon | Two agencies reporting one fire would inflate counts; border/water points are often legit | counts in figures/a_qa_counts.csv | — |
| 5 | 2026-11-25 | MTBS gap metric = share of fires and acres with FIRE_SIZE < 500 ac | MTBS maps fires ≥ 500 ac in the eastern US (≥ 1,000 ac West) | 500 ac | USGS EROS MTBS page: usgs.gov/centers/eros/science/monitoring-trends-burn-severity |
| 6 | 2026-11-25 | State boundaries: Census 2023 cartographic boundary, 1:20M; maps and density in EPSG:5070 (CONUS Albers equal-area); hex ~10 km | Equal-area projection so hex counts compare fairly across latitudes | 10 km hex | www2.census.gov/geo/tiger/GENZ2023 |
| 7 | 2026-11-25 | Part C RAWS source = USFS FEMS (not Synoptic as in the brief). Hourly CSV via `ext-climatology/download-weather`; stations via `stationMetaData` GraphQL; values with QC flag 2 ("suspicious") set to NaN and counted | Synoptic historical access now needs a paid plan or a .edu Open Access account; FEMS is free, the USFS system of record for RAWS and NFDRS, and ships QC flags | — | FEMS Climatology API External User Guide (2025-09); FEMS TechNote 2025-09-16 |
