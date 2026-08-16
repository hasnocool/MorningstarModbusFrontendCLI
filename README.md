# MorningstarModbusFrontendCLI

A keyboard-first terminal operations dashboard for [MorningstarModbusAPI](https://github.com/hasnocool/MorningstarModbusAPI).

**Current version: v0.5.0**

The frontend is intentionally API-only. It does not probe serial ports, open Modbus connections, access the telemetry SQLite database, or expose controller writes. MorningstarModbusAPI remains the authority for hardware discovery, immutable `controller_uid` identity, source-backed register semantics, history reconciliation, site aggregation, incidents and forecasting.

## What v0.5 includes

- **v0.1 foundation:** async HTTP client, SSE, reconnect/backoff, controller inventory and console snapshot mode.
- **v0.2 operations:** overview, controller inventory, power flow, energy ledger, event timeline and Unicode history charts.
- **v0.3 intelligence:** persistent incidents, evidence, health scores, local solar forecast, Float probability and forecast backtesting.
- **v0.4 investigation:** a movable historical cursor with correlated normalized telemetry and events.
- **v0.5 NOC:** concurrent multi-site supervision, compact/low-bandwidth/alert-only modes and text/JSON snapshots.

## Requirements

- Python 3.12+
- MorningstarModbusAPI reachable over HTTP(S)
- Textual 8.2.8+
- HTTPX 0.28.1+

## Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp config.example.toml config.toml
```

Start MorningstarModbusAPI separately, then run:

```bash
morningstar-tui --config config.toml
```

For a single plain-text health snapshot:

```bash
morningstar-tui --config config.toml --snapshot
```

For machine-readable output:

```bash
morningstar-tui --config config.toml --snapshot --json
```

## Keyboard navigation

| Key | View/action |
| --- | --- |
| `1` | Overview |
| `2` | Controllers |
| `3` | Power flow |
| `4` | Incidents |
| `5` | Forecast |
| `6` | History |
| `7` | Events |
| `8` | Investigation |
| `9` | Multi-site NOC |
| `Tab` / `Shift+Tab` | Next/previous site |
| `[` / `]` | Shorter/longer history window |
| `m` | Cycle history metric |
| `t` | Investigation cursor = now |
| `-` / `+` | Investigation cursor -/+ 5 minutes |
| `PageUp` / `PageDown` | Investigation cursor -/+ 1 hour |
| `r` | Immediate REST refresh |
| `q` | Quit |

## Multi-site configuration

```toml
[dashboard]
refresh_interval_seconds = 15.0
history_window = "24h"
history_metric = "solar_input_power_w"

[[sites]]
name = "trailer"
base_url = "http://127.0.0.1:8080"
system = "sys_default"

[[sites]]
name = "cabin"
base_url = "https://solar-cabin.example.net"
system = "sys_default"
```

The NOC view shows each API's connectivity, SSE state, health score, solar input, battery voltage, active incident count and latency.

## Constrained links

`--low-bandwidth` raises the REST enrichment interval to at least 60 seconds while keeping the efficient SSE stream for live changes.

`--alert-only` disables continuous SSE and periodically refreshes incident/health/forecast state. Use this when second-by-second telemetry is less important than minimizing network traffic.

```bash
morningstar-tui --config config.toml --low-bandwidth
morningstar-tui --config config.toml --alert-only
```

## History and Storage v2

The frontend never reads archive files directly. It requests the documented system history endpoint at an appropriate resolution:

- 1h → 1-minute buckets
- 6h/24h → 5-minute buckets
- 7d/30d → 1-hour buckets
- 180d/1y → 1-day buckets

This keeps the TUI independent of MorningstarModbusAPI's hot/warm/cool/cold storage implementation.

## Predictive operations

The Forecast view consumes the API's offline-first forecast resources. It displays historical percentile bands and confidence instead of turning a probabilistic estimate into a guaranteed outcome. If the API reports insufficient evidence, the TUI shows missing/unknown values rather than inventing a prediction.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
python -m compileall -q src tests
pytest
```

See [docs/architecture.md](docs/architecture.md) for the concurrency model and [docs/roadmap.md](docs/roadmap.md) for the implemented v0.1-v0.5 scope.
