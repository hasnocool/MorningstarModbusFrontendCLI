# MorningstarModbusFrontendCLI

Keyboard-first terminal operations dashboard for [MorningstarModbusAPI](https://github.com/hasnocool/MorningstarModbusAPI).

**Current version: v0.8.0**

The frontend remains API-only and read-only: it does not probe serial ports, open Modbus connections, access the telemetry database directly, or expose controller writes.

## Release progression

- **v0.6 Data Integrity + Controller Drill-down** — controller evidence coverage, recovered/partial/missing gaps, retained-history status and controller-vs-local energy verification.
- **v0.7 Operator Workflow + Command Palette** — searchable commands, breadcrumbs, back navigation and controller workflow shortcuts.
- **v0.8 Fleet Comparison / Long-term Analytics** — cross-site/controller 90-day evidence quality plus 30/90-day energy comparison.

## Keyboard navigation

| Key | Action |
| --- | --- |
| `1`..`9` | Existing overview/controllers/power/incidents/forecast/history/events/investigation/NOC views |
| `Enter` | Open highlighted controller row |
| `d` | Selected controller operations |
| `f` | Fleet comparison / long-term analytics |
| `Ctrl+P` or `/` | Command palette |
| `Esc` | Back |
| `Tab` / `Shift+Tab` | Next/previous site |
| `r` | Refresh selected site (and controller evidence when relevant) |
| `q` | Quit |

## Data-integrity workflow

Open **Controllers**, highlight a physical `controller_uid`, and press **Enter**. The controller operations screen loads API v0.6 evidence asynchronously and shows:

- live and daily evidence coverage;
- recovered, partial and missing history gaps;
- controller-retained history synchronization status;
- 30-day controller-reported vs locally integrated energy;
- skipped/quality information for daily integrations;
- 90-day controller energy totals.

No missing high-frequency samples are fabricated.

## Fleet analytics

Press **f** to hydrate controller analytics across configured sites with bounded concurrency. The fleet screen compares API availability, health, incident counts, evidence coverage, 30/90-day controller energy and 30-day energy discrepancy.

## Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp config.example.toml config.toml
morningstar-tui --config config.toml
```

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
python -m compileall -q src tests
pytest
```
