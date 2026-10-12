# Cross-Market Research Case Studies

Two exploratory studies test whether historical cross-market association survives a chronological forecast evaluation. Both use genuine latest-revised FRED observations, weekly percentage returns, and the Cross-Market Correlation Research Engine.

**Finding:** strong same-week dependence did not produce a successful lagged forecast in either study. Negative results are retained rather than filtered out.

## Results at a glance

| Study | Same-week correlation | Approximate 95% bootstrap interval | Selected lag | Holdout correlation | MSE skill versus frozen training mean |
| --- | ---: | --- | ---: | ---: | ---: |
| [EUR/USD → USD/JPY](case_studies/eurusd_usdjpy/report.html) | -0.475 | [-0.573, -0.358] | 7 weeks | +0.034 | -0.65% |
| [EUR/USD → Broad US dollar](case_studies/eurusd_broad_dollar/report.html) | -0.869 | [-0.895, -0.835] | 1 week | +0.082 | -3.50% |

Negative skill means higher forecast squared error than the baseline. Correlation strength is not forecast accuracy. GitHub may display HTML source: download a report and open it in a browser to view its formatted contents.

## Shared method

- Sample interval: 7 January 2022–9 October 2026; 249 weekly bins and 247 overlapping same-week returns.
- FRED series: DEXUSEU (USD per euro), DEXJPUS (yen per USD), and DTWEXBGS (Broad US dollar index).
- Pearson correlations; circular-block bootstrap with block length 5, 500 replicates, seed 42 and approximate 95% percentile intervals.
- Breakdown analysis compares adjacent 60-week windows; prior window 28 June 2024–15 August 2025, recent window 22 August 2025–9 October 2026.
- First 70% of sampled periods reserved for training, ending 2 May 2025. Positive lags 1–8 weeks are scanned using training data only; the largest absolute training correlation selects the lag.
- OLS intercept and slope are fitted on training observations and frozen. An eight-period embargo follows training; the holdout begins 4 July 2025 and contains 66 valid forecast/actual pairs.
- Forecasts are compared with the target's frozen training-mean forecast using mean squared error (MSE). Skill = 1 − model MSE / baseline MSE.
- Arrow direction denotes the selected forecast setup, not causality.

## Study 1: EUR/USD → USD/JPY

**Question.** Is there an inverse same-week relationship, and can earlier EUR/USD weekly returns help forecast later USD/JPY weekly returns?

**Hypothesis evaluated.** A training-selected positive lag provides lower holdout MSE than a frozen training-mean forecast. This question summarises an exploratory study; no preregistration is claimed.

**Results.** Same-week correlation was -0.475. The recent correlation was more negative (-0.636) than the prior correlation (-0.488), but the approximate interval for the change, [-0.395, +0.048], included zero. The training scan selected lag 7 with correlation +0.115. Holdout correlation fell to +0.034. Model MSE was 1.191878, versus baseline MSE 1.184177, producing -0.65% skill.

**Conclusion.** The sample contains inverse contemporaneous association, but this selected lag did not beat the forecast benchmark. The window comparison does not clearly establish a correlation change under this method.

**Evidence.** [Report](case_studies/eurusd_usdjpy/report.html) · [Settings and results](case_studies/eurusd_usdjpy/manifest.json)

## Study 2: EUR/USD → Broad US dollar

**Question.** Does strong inverse same-week dependence translate into useful prediction of later broad-dollar returns from earlier EUR/USD returns?

**Hypothesis evaluated.** A training-selected positive lag provides lower holdout MSE than a frozen training-mean forecast. No preregistration is claimed.

**Results.** Same-week correlation was -0.869. The prior correlation was -0.898 and the recent correlation -0.953. The change was -0.055, with approximate interval [-0.097, -0.017], excluding zero under the independent-window bootstrap. The selected lag was 1 week, with training correlation -0.138. Holdout correlation was +0.082. Model MSE was 0.348221, versus baseline MSE 0.336446, producing -3.50% skill.

**Conclusion.** The same-week association was strong and became more negative in the recent window. The lagged relationship was weak, reversed sign in the holdout and failed to improve forecast error. The change interval is an exploratory screening result, not proof of a new regime.

**Evidence.** [Report](case_studies/eurusd_broad_dollar/report.html) · [Settings and results](case_studies/eurusd_broad_dollar/manifest.json)

## Limitations and research discipline

These are latest-revised observations, not point-in-time publication vintages. Observation timestamps do not establish historical availability. The results support dependence research, not a tradable macro backtest.

Intervals depend on sample choice, block length and local stationarity assumptions. The breakdown bootstrap treats windows independently and ignores dependence across their boundary. No multiple-testing-adjusted significance claims are made. Shared dollar exposure and FX quotation direction should be considered before interpreting inverse correlations as independent economic information.

These two studies use the same evaluation period and are not independent replications. Repeatedly changing pairs, transforms or lags after reviewing the holdout turns that period into development data. Further final confirmation requires a new reserved sample. The engine does not model execution, costs, sizing or portfolio returns.

## Reproducibility

The committed HTML reports include settings, results, panel SHA-256 hashes, bootstrap draws, training lag scans and holdout forecast tables. Their adjacent manifest.json files are extracted directly from those reports.

Preserve each dashboard research ZIP's transformed_panel.csv and exported tables alongside the report when available. Those source exports are not reconstructed here: an HTML report alone does not contain the complete transformed panel used for the same-week study. Hashes identify the original panels but cannot restore them. Refreshing FRED may change observations and therefore results.

For a new study, use `research_cli.py` with a frozen CSV, explicit pair, frequency, transforms and seed. Keep the original exports for exact reproduction of these studies.

## Engineering evidence

The release includes a modular calculation engine, input checks, reproducible random seeds, missing-data handling, sample-overlap gates, stale-result detection, report exports and 18 passing unit tests at release validation. A regression test verifies that changing holdout outcomes cannot change the training-selected lag or fitted coefficients.
