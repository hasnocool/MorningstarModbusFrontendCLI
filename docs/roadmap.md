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
