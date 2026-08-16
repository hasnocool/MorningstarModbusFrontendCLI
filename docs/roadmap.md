# Implemented roadmap

## v0.1 — TUI foundation

- Python 3.12+ package and console entry point.
- Async HTTPX client.
- Native SSE parser and live system stream.
- Reconnect/backoff and connection state.
- Controller inventory and selected-site overview.
- ANSI-free `--snapshot` mode for scripts/SSH health checks.

## v0.2 — Site operations

- System overview.
- Controller inventory.
- Power-flow and energy-ledger rendering.
- Unicode historical plots.
- Multi-resolution history windows from 1 hour to 1 year.
- Unified event timeline.

## v0.3 — Predictive operations

- Persistent incident command center.
- Evidence display.
- System health score.
- Solar forecast P10/P50/P90 curves.
- End-of-day energy outlook.
- Float probability and expected Float time.
- Forecast calibration/backtest summary.

## v0.4 — Investigation console

- Movable UTC time cursor.
- Bounded before/after window.
- Correlated solar, charge, battery and charge-state history.
- Events in the investigation window.
- Five-minute and one-hour cursor movement.

## v0.5 — Terminal NOC

- Multiple API sites from one TOML file.
- Concurrent per-site supervision.
- NOC summary with health/solar/battery/incidents/latency.
- Site switching from the keyboard.
- Compact configuration flag.
- Low-bandwidth mode.
- Alert-only mode.
- tmux/SSH-friendly terminal-only operation.
- JSON or text one-shot snapshots for monitoring integration.

## v0.6 — Data Integrity + Controller Drill-down

- Interactive controller drill-down from the physical-controller inventory.
- 90-day live/daily evidence coverage.
- Recovered/partial/missing gap reconciliation.
- Controller-retained history summary and synchronization visibility.
- Controller-reported vs locally integrated 30-day energy verification.
- 90-day controller energy rollup.
- Lazy bounded async enrichment and short-lived controller cache.
- NOC observability-health indicators for data coverage and energy discrepancy.

## v0.7 — Operator Workflow + Command Palette

- Searchable keyboard command palette (`Ctrl+P` or `/`).
- Breadcrumb-like site/system/view location in the app subtitle.
- Navigation stack with `Esc` back behavior.
- Controller inventory → controller operations workflow.
- Palette actions for site, investigation, controller and fleet operations.

## v0.8 — Fleet Comparison / Long-term Analytics

- Fleet/site comparison screen.
- Per-controller and per-site 90-day evidence quality.
- 30-day and 90-day controller energy comparison.
- Fleet-wide energy discrepancy visibility.
- Bounded concurrent fleet hydration so large site lists do not stampede APIs.
