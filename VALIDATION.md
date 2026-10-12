Cross-Market Research Engine v2 — validated 12 October 2026

- 18 unit tests passed, including deterministic resampling, missing dates, constant-series rejection, known lag recovery, holdout isolation and report packaging.
- Streamlit AppTest: app started, research form ran without exceptions, all three research components returned, changed inputs marked results stale.
- Genuine FRED EUR/USD and broad-dollar CSV download and command-line study completed.
- Live-data example: weekly contemporaneous correlation -0.869; percentile interval [-0.896, -0.837]; training-selected positive lag 1; holdout MSE skill -3.61% against training-mean baseline. This is negative predictive skill, not evidence of a trading edge.
- Browser visual review and Windows installation were not performed in this environment.
- Dependencies tested:
  - numpy: 2.3.5
  - pandas: 2.2.3
  - streamlit: 1.65.0
  - plotly: 6.9.0
  - duckdb: 1.5.6
  - scipy: 1.17.0