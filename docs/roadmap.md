# Implemented roadmap

## v0.1-v0.5

Foundation, site operations, predictive operations, investigation/time travel and multi-site NOC.

## v0.6 — Data Integrity + Controller Drill-down

- Interactive controller drill-down from the inventory.
- 90-day live/daily evidence coverage.
- Recovered/partial/missing gap reconciliation.
- Controller-retained history summary.
- Controller-reported vs locally integrated 30-day energy verification.
- 90-day energy rollup.
- Lazy bounded async enrichment and cache.
- NOC observability-health indicators.

## v0.7 — Operator Workflow + Command Palette

- Searchable keyboard command palette (`Ctrl+P` or `/`).
- Breadcrumb-like location in the app subtitle.
- Navigation stack with `Esc` back behavior.
- Controller inventory → controller operations workflow.
- Palette actions for site, investigation, controller and fleet operations.

## v0.8 — Fleet Comparison / Long-term Analytics

- Fleet/site comparison screen.
- Per-controller and per-site 90-day evidence quality.
- 30-day and 90-day controller energy comparison.
- Fleet-wide energy discrepancy visibility.
- Bounded concurrent fleet hydration so large site lists do not stampede APIs.
