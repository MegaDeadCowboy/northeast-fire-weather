# Project Brief: Northeast Fire & Weather Data Assessment

**Owner:** Carver Rasmussen
**Drafted:** Nov 24, 2026
**Build day:** Nov 25, 2026 (one full day for the core; day 2 for the StoryMap and polish)
**Target application:** USDA-FS Fire and Weather Analysis Hub Research Fellowship (ORISE USDA-FS-NRS-2026-0434). Mentor: Erin Lane, USDA Northeast Climate Hub. Closes Jan 1, 2027, rolling review.

---

## 1. Why this project

The fellowship's research project is to study fire occurrence and weather data in the Northeast. That means finding, evaluating and synthesizing datasets, working out what data partners need, and presenting the results. This project is a small version of that job, done before applying, on public data.

The posting's preferred skills are remote sensing, geospatial analysis and ArcGIS Pro/QGIS. The project builds on two finished repos:

- **fire-weather-windows** (PNW): 15 RAWS stations, Synoptic Data + NOAA NDFD APIs, prescribed-burn threshold logic, Streamlit dashboard. Main finding: humidity and wind are the binding constraints, and temperature almost never is.
- **jasper-burn-severity**: Sentinel-2 dNBR, validation against an official perimeter, recovery tracking, decision log.

**One-sentence pitch:** *"I took my PNW burn-window tool to the Northeast, matched 29 years of Northeast fires to fire-danger conditions at ignition, and mapped where the region's fire and weather data fall short."*

## 2. Study region

The USDA Northeast Climate Hub region: **12 Northeast states plus DC, from Maine to West Virginia**. Confirm the exact state list on the Hub's About page and record it in the decision log.

Candidate list to verify: ME, NH, VT, MA, RI, CT, NY, NJ, PA, DE, MD, WV, plus DC.

## 3. Research questions

1. **When and where do Northeast wildfires happen?** Seasonality by state, size distribution and cause, 1992–2020.
2. **What were fire-danger conditions at ignition?** For each fire, how did Energy Release Component (ERC) and 100-hour fuel moisture on the discovery date compare with that location's own climatology? Do Northeast fires cluster in the spring window before leaf-out?
3. **What limits prescribed-burn windows in the Northeast?** Rerun the fire-weather-windows logic on Northeast stations and compare the binding constraints with the PNW result.
4. **Where are the data gaps?** Inventory the main fire and weather datasets for the region, covering coverage, resolution, timeliness and known gaps, and map weather-station density.

## 4. Data sources

| Dataset | What it gives | Access | Notes |
|---|---|---|---|
| **FPA FOD 6th edition** (Short 2022, RDS-2013-0009.6) | Point record per wildfire: discovery date, final size, cause, location | USFS Research Data Archive: download the **GeoPackage or SQLite** version | Covers 1992–2020. ~2.3M records nationally. Filter to the study states first |
| **gridMET** | Daily ~4 km weather and fire-danger grids: ERC, BI, FM100, FM1000, RH min/max, wind, VPD | Google Earth Engine `IDAHO_EPSCOR/GRIDMET`, or Climatology Lab netCDF | Runs 1979 to near-present, CONUS only. Recent days are provisional |
| **RAWS / Synoptic Data API** | Hourly station observations | Reuse the fire-weather-windows client and API token | Find the Northeast RAWS stations with a full year of hourly data. Station sparsity is itself a finding |
| **MTBS** | Burn-severity perimeters for large fires | mtbs.gov | Maps only fires ≥ 500 acres in the East (≥ 1,000 in the West). Used here for the gaps analysis, not as an input |
| **Northeast Climate Hub state list** | Region definition | climatehubs.usda.gov/hubs/northeast/about | For the study-area boundary |
| **State boundaries** | Basemap and clip | Census TIGER cartographic boundaries | |

Optional (day 2): NASA FIRMS (MODIS/VIIRS active fire detections), to compare satellite detections with reported fires.

## 5. Scope

**In scope (day 1):**
- Fire occurrence summary for the region (Q1)
- Ignition-day fire danger for a defined subset of fires (Q2)
- Burn-window rerun on 3–6 Northeast stations (Q3)
- Data landscape table plus station-density map (Q4)
- Quarto report and README with a decision log

**Out of scope:**
- Fire spread or behavior modeling
- Burn-severity mapping (that's Jasper's job)
- Forecasting
- Agricultural burning
- Anything outside the Northeast region

**Day 2 (stretch):**
- ArcGIS StoryMap for a general audience
- FIRMS vs FPA FOD detection comparison
- Streamlit page for the Northeast stations

## 6. Methods

### Part A: Fire occurrence (Q1)
1. Load FPA FOD from the GeoPackage/SQLite and filter to the study states. Keep discovery date, discovery day of year, fire size, size class, cause, state, lat/lon.
2. QA: drop or flag records with missing dates or coordinates, and log the counts. Check for duplicate records.
3. Summaries:
   - Fires per month (all years pooled) by state
   - Size distribution, including the **share of fires and of area burned below 500 acres**. This number feeds the MTBS gap in Part D.
   - Cause breakdown
4. Figures: a monthly seasonality chart and a fire-density map (hex bins or kernel density).

### Part B: Fire danger at ignition (Q2)
1. **Subset for tractability:** fires ≥ 10 acres, or all fires in 2–3 contrasting states (for example NJ Pine Barrens, PA, ME). Pick one, record why in the decision log, and keep the subset size manageable for one day.
2. For each fire, extract gridMET **ERC** and **FM100** at the fire point on the discovery date. Use Earth Engine `sampleRegions` in batches, or read the netCDF locally.
3. Express each as a **percentile against that grid cell's own 1992–2020 climatology for the same calendar window**, so a spring fire in Maine is compared with Maine in spring.
4. Compare spring (Mar–May) and summer/fall fires. Test whether ignition-day ERC percentiles sit above the median.

### Part C: Northeast burn windows (Q3)
1. Find Northeast RAWS stations through Synoptic. Choose 3–6 with a full recent year of hourly data, spread across states and forest types.
2. **Burn prescription thresholds:** don't reuse the PNW USFS thresholds. Find a published Northeast prescribed-fire prescription (a state forestry agency, The Nature Conservancy Northeast, or a National Forest burn plan) and cite it. If none is usable, run the PNW thresholds and say so plainly.
3. Reuse the fire-weather-windows threshold logic, adding a `regions/northeast` config so the repo supports multiple regions.
4. Output: hours per month inside the window, and which constraint fails most often (RH, wind, temperature, precipitation). **Headline:** is the binding constraint the same as the PNW's?

### Part D: Data landscape and gaps (Q4)
A table with one row per dataset and these columns:
- What it measures
- Spatial resolution / unit
- Temporal coverage and latency
- Northeast-specific limitations
- Who it serves

Datasets to cover:
- FPA FOD
- gridMET
- RAWS
- MTBS
- FIRMS
- the state fire reporting systems behind FPA FOD

Plus a **station-density map**: RAWS stations per state or per 10,000 km² of forest, against the fire-density map from Part A. Close with 3–5 one-line data needs, each backed by a number from Parts A–C. This mirrors the "assess and communicate regional data needs" line in the posting.

## 7. Deliverables

1. **Repo:** `northeast-fire-weather` (new) for Parts A, B and D. Part C lives in **fire-weather-windows** as a second region, linked both ways.
   ```
   northeast-fire-weather/
     README.md            key results table up top, like Jasper
     docs/project_brief.md
     docs/decision_log.md
     notebooks/01_fpa_fod.ipynb      Part A
     notebooks/02_ignition_danger.ipynb   Part B
     notebooks/03_data_landscape.ipynb    Part D
     src/                 shared helpers
     figures/             PNGs + CSVs behind every number
     report/northeast_fire_weather.qmd    Quarto report
   ```
2. **Quarto report:** 4–6 pages, one section per question, with a limitations section.
3. **README:** a key-results table at the top, with every number traceable to a CSV in `figures/`.
4. **Day 2:** an ArcGIS StoryMap with 4 maps and 3 findings, written for non-technical partners.

## 8. Day plan (Nov 25)

| Block | Time | Work |
|---|---|---|
| 1 | 0:00–0:45 | Create the repo, download FPA FOD (GeoPackage), confirm the state list, set up Earth Engine auth |
| 2 | 0:45–2:45 | **Part A:** filter, QA, seasonality, size distribution, density map |
| 3 | 2:45–4:45 | **Part C:** find Northeast stations, find thresholds, add the Northeast config, run windows |
| 4 | 4:45–6:45 | **Part B:** pick the subset, extract gridMET, compute percentiles, spring vs summer comparison |
| 5 | 6:45–8:15 | **Part D:** dataset table, station-density map, data-needs list |
| 6 | 8:15–9:45 | Quarto report, README results table, decision log, push |

**Cut order if time runs short:** Part B goes down to one state → Part C goes down to 3 stations → drop the station-density map and keep the table.

## 9. Done when

- [ ] Every number in the README traces to a CSV in `figures/`
- [ ] The decision log records each method choice with its reason: state list, fire subset, thresholds source, climatology window
- [ ] Limitations section covers at least the following:
  - FPA FOD ends in 2020
  - Gaps in state reporting
  - gridMET's 4 km cells vs point fires
  - Few Northeast RAWS stations
  - Thresholds source
- [ ] Quarto report renders
- [ ] Repo is public with a license (code MIT, derived data CC BY 4.0)
- [ ] One resume bullet and one cover-letter sentence drafted from the real results

## 10. Open questions to settle early

1. Is FPA FOD still the newest edition (6th, through 2020)? Check the RDS archive for a 7th edition.
2. How many Northeast RAWS stations have a full recent year of hourly data?
3. Where to get Northeast burn-prescription thresholds?
4. Earth Engine or local netCDF for gridMET? Whichever is faster to authenticate tomorrow.

## 11. How it plugs into the application

- **Email to Erin Lane** (once Parts A and C exist): two lines plus the repo link. Don't wait for the StoryMap.
- **Resume:** replaces Whatcom Creek or WERAP as the third project for this application. Lead with Fire Weather Windows + this project, then Jasper.
- **Essay hooks:**
  - The PNW vs Northeast binding-constraint contrast
  - The share of Northeast fires that MTBS misses
  - The station-density gap
- **Still blocking regardless:** two recommenders.
