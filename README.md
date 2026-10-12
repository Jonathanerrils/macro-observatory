# Cross-Market Correlation Research Engine / Macro Observatory v2

See [UPGRADE.md](UPGRADE.md) for upgrading an existing installation, research methodology and GitHub commands. The Research validation tab adds block-bootstrap uncertainty, correlation change intervals, and frozen chronological holdout forecasts.

# Macro Observatory — overnight MVP

A local Python research dashboard and correlation engine. Start with a clearly labelled synthetic demo, fetch latest FRED snapshots, or upload a wide CSV. No paid service or API key is required for the included FRED CSV adapter.

## Windows quick start (PowerShell, Python 3.11+)

Extract this folder, open it in VS Code and open a terminal there:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard opens in your browser. Leave the terminal running. Ctrl+C stops it.

On macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

## First session

1. Use Synthetic demo to check the interface; it contains no actual market history.
2. Choose FRED series in the sidebar and click Refresh snapshot.
3. Switch to Saved FRED snapshot. Failed series are reported individually. The saved panel contains only successful series from that refresh, not silently reused old data.
4. Use weekly sampling for the daily cross-market universe. Analyse monthly economic indicators separately at monthly frequency; they will not be forward filled into daily returns.
5. Review transforms, overlap counts and data quality before interpreting correlations.
6. Export the transformed panel, matrix, sample counts and settings for reproducibility.

Uploaded CSV format:

```csv
date,EURUSD,US2Y
2026-01-02,1.170,3.50
2026-01-05,1.172,3.52
```

Dates must be unique and values numeric; blank cells represent missing observations. Custom series default to first differences: select the appropriate transform explicitly. Percent returns are in percent; yield differences remain percentage points. WTI/Brent use differences by default because historical oil prices can be nonpositive.

## Included

- US macro/rate indicators, major currency crosses, broad dollar, equity, oil and VIX starter catalog.
- Pearson and Spearman pairwise correlations with overlap gates and counts.
- Rolling correlation using complete consecutive sample windows.
- Non-overlapping recent/prior comparison and descriptive change flag.
- Exploratory lead/lag scanning with clear lag direction.
- Missingness, latest dates, age and constant-series checks.
- Immutable timestamped raw FRED files, source URLs and SHA-256 manifests.
- DuckDB snapshot history; current wide panel at data/latest.csv.
- CSV uploads and research exports; offline synthetic demonstration.

## Scope and statistical limits

This is a working MVP, not a completed institutional platform. The catalog is US-focused with international currency crosses, not comprehensive global economic coverage. Synthetic relationships are constructed and cannot support any market claim.

FRED observations are latest revised values. Retrieval timestamps and hashes preserve what was downloaded but do not reconstruct historical publication vintages. Monthly observation dates are not release dates. Do not use this panel for point-in-time trading backtests. A next phase must add release timestamps and ALFRED vintage data.

Resampling uses the last available observation in each sample bin. Different markets may have different closing times and holidays. No forward filling occurs. Pairwise matrices can be non-positive-semidefinite because pairs use different observations: do not feed them directly into a portfolio optimizer. The rolling calculation requires every period in its window to have both observations; sparse data can therefore produce empty plots.

Correlations and lead/lag scans are descriptive, not causal or verified forecasts. The v2 research tab adds approximate block-bootstrap intervals and one chronological holdout. Multiple testing and repeated tuning remain unresolved; no corrected significance claims are made. Recent/prior change threshold 0.30 is a UI heuristic, not a calibrated regime detector. Level correlations can be spurious. This version does not execute trades.

## Overnight completion plan

- Install and run locally; verify demo and imports.
- Refresh a small daily universe; inspect freshness and failed downloads.
- Test a pair such as EUR/USD and the broad dollar, then export its results.
- Add one genuine dataset you already have using CSV import.
- Capture the interface and document a reproducible research question for the portfolio.

## Next phases

1. Add ECB euro-area rates/inflation, IMF/World Bank country panels, and explicit frequency/unit/release metadata.
2. Add ALFRED vintages and an as-of join layer, then validate point-in-time semantics.
3. Extend the included bootstrap and chronological holdout with block-length sensitivity, multiple-testing controls and walk-forward prediction tests.
4. Add EUR/USD differential features and separate valuation, catalyst, timing and risk views.
5. Add provider integration tests, scheduling, logging and operational monitoring.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

FRED source documentation: https://fred.stlouisfed.org/help/data/downloading/using-the-download-data-link/
FRED observations/vintages: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
Streamlit: https://docs.streamlit.io/

Dependencies are bounded major-version ranges, not an exact environment lock. A successful local install should be recorded with `python -m pip freeze` before extending the project.
