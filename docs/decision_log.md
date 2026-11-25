# Decision Log

Each entry: what was chosen, why, the number behind it, and the source.

| # | Date | Decision | Why | Number | Source |
|---|---|---|---|---|---|
| 1 | 2026-11-25 | New repo `northeast-fire-weather` for Parts A, B, D; Part C goes in fire-weather-windows as `regions/northeast` | Per brief §7 | — | docs/project_brief.md |
| 2 | 2026-11-25 | Study region = CT, DE, MD, ME, MA, NH, NJ, NY, PA, RI, VT, WV + DC | Hub About page gives only "twelve Northeastern States plus DC"; USDA's Northeast Hub page names them | 12 states + DC | climatehubs.usda.gov/hubs/northeast/about; usda.gov/node/19049 |
| 3 | 2026-11-25 | Use FPA FOD **7th edition** (FPA_FOD_20260615, 1992–2024), GeoPackage, not the 6th (1992–2020) in the brief | Brief open question #1: the 7th edition is out; 4 more years of data, same format. Brief text "29 years / ends 2020" becomes 33 years / ends 2024 | 2.66M records nationally; GPKG zip 227.14 MB | Short 2026, doi:10.2737/RDS-2013-0009.7 |
