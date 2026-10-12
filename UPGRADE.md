# Cross-Market Research Engine — v2

## Upgrade your existing Windows project

1. Stop Streamlit with Ctrl+C in its terminal.
2. Extract this archive into a separate temporary directory.
3. Copy the CONTENTS of its `global_macro` folder into your existing `global_macro` folder, replacing matching source files. Keep your existing `.venv`, `data`, and `.git` directories. The archive intentionally excludes runtime data and virtual environments.
4. From the parent `Macro_Observatory_MVP` directory, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\global_macro\requirements.txt
cd .\global_macro
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
..\.venv\Scripts\python.exe -m streamlit run app.py
```

If your virtual environment is INSIDE `global_macro`, use `.\.venv\Scripts\python.exe` instead of `..\.venv\Scripts\python.exe` after changing directory.

Open the new **Research validation** tab. Select a pair, review frequency and transforms in the sidebar, and click **Run research**. Results are retained across download-button reruns but marked stale when inputs change.

## Included research features

- Reproducible circular-block bootstrap with 95% percentile intervals, paired row resampling and missing calendar bins preserved.
- Non-overlapping adjacent windows with approximate uncertainty on correlation change.
- Positive lag selection using training data only, maximum-lag embargo, frozen OLS coefficients, chronological holdout and frozen training-mean benchmark.
- MSE skill distinguishes association from forecast performance; a negative value means the forecast loses to the benchmark.
- Downloadable HTML report, JSON settings/results, panel SHA-256, transformed panel, training scan, bootstrap draws and holdout forecasts.
- Headless command-line reproduction and regression tests.

## Reproduce a study

From `global_macro`, with your Python environment activated:

```powershell
python research_cli.py --csv data/latest.csv --driver DEXUSEU --target DTWEXBGS --output research_outputs/eurusd_dollar.zip
```

Omit `--csv` to demonstrate using synthetic observations. Use `--help` for frequency, transforms, seed and sample controls. The CLI fails explicitly if any study component lacks enough coverage; the UI reports each component independently.

## Research interpretation

This is an exploratory research release. Block length should be chosen before inspecting results and sensitivity assessed on development data. Circular blocks preserve short-range dependence within blocks, with end-to-start wraparound. Percentile intervals have approximate coverage under stationarity/mixing assumptions; they are not guaranteed for structural breaks or small samples.

The difference interval resamples each window independently and ignores cross-boundary dependence. It is a descriptive screening tool. No multiple-testing-adjusted significance claims are made. Scanning many pairs or repeatedly changing lags/windows invalidates any claim of a pristine holdout; reserve a new external sample for final confirmation.

Spearman controls the lag-selection score if selected, but the forecast remains OLS on the actual transformed values. Lead/lag is in sampling periods, not clock time. Lag one for weekly sampling means the previous weekly bin. Observation dates do not imply publication availability. Latest revised macro data remain unsuitable for historical trading backtests.

The report is a downloadable HTML file that can be opened and printed from a browser; it is not a PDF generator. Forecasts are transformed-value estimates, not executable trading signals, and have no costs/position-sizing model.

Method references:
- https://bashtage.github.io/arch/bootstrap/timeseries-bootstraps.html
- https://bashtage.github.io/arch/bootstrap/confidence-intervals.html

## GitHub update

Run inside your existing repository after reviewing files:

```powershell
git status
git add app.py macro/research.py macro/research_ui.py research_cli.py tests/test_research.py requirements.txt README.md UPGRADE.md VALIDATION.md .gitignore
git commit -m "Add cross-market uncertainty and chronological holdout research"
git push
```

Do not copy a `.git` directory from another project. Data, local secrets and generated research outputs are excluded by `.gitignore`.
