# Benchmark Latest (2026-03-27)

## Environment
- Python: 3.12.10 (venv)
- Command:
  - `c:/gemini-desktop/gemini/.venv/Scripts/python.exe benchmark_optimizations.py`

## Results
- BacktestEngineV2.run (20k bars, real code)
  - old: 0.4495s
  - new: 0.0569s
  - speedup: 7.91x

- Legacy execution engine.run (20k bars, real loop)
  - old: 0.3518s
  - new: 0.0304s
  - speedup: 11.57x

- PortfolioEngine max_positions break (micro benchmark, 200 tickers)
  - old: 0.0157s
  - new: 0.0004s
  - speedup: 42.44x

## Notes
- Values are from median runtime in benchmark_optimizations.py output.
- Keep this file updated after major hot-path refactors.
