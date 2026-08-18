# Changelog

## 0.9.0 - 2026-08-16

### Added

- Reorganized SYSTEM, CONTROLLER, HISTORY and SITE/FLEET operator workspaces with a persistent navigation strip.
- Full system/site details workspace exposing the normalized metric catalog, system energy, health and baselines.
- Full live telemetry explorer for normalized system data and selected-controller data, including units, quality and source metadata when present.
- Topology/component graph workspace with components, relationships, confidence and evidence.
- Controller diagnostics workspace exposing health evidence, charge-cycle/forecast detail, polling performance/history, raw history summary, incidents and recent samples.
- Generic defensive payload explorer so new backend fields can become visible without duplicating register semantics in the frontend.
- Separate lazy site-details and controller-diagnostics hydration paths with bounded async concurrency.

### Changed

- Controller activation now opens the full live telemetry workspace; data integrity and diagnostics are sibling controller workspaces.
- Overview now includes substantially more electrical and health state, including whole-system current/power fields when available.
- Power / Energy now includes whole-system charge/battery/load currents, power residuals, additional Ah/Wh counters and provenance detail.
- Controller inventory now includes serial, firmware and last-seen metadata.
- Command palette is grouped by operator context and includes the new workspaces.
- Version advanced from 0.8.0 to 0.9.0.

## 0.8.0 - 2026-08-16

### Added

- v0.6 controller drill-down with coverage, gap reconciliation, retained-history and independent energy verification.
- Lazy, bounded controller analytics cache with atomic async state updates.
- v0.7 searchable command palette, navigation stack, breadcrumbs and controller workflow shortcuts.
- v0.8 fleet comparison with per-site and per-controller 30/90-day energy and 90-day evidence coverage.
- Observability-health columns in the multi-site NOC.

### Changed

- Controller inventory now surfaces data coverage and energy discrepancy when enriched.
- Version advanced from 0.5.0 to 0.8.0.

## 0.5.0 - 2026-08-16

Initial implementation through the v0.5 roadmap.

### Added

- Async multi-site MorningstarModbusAPI client and SSE streaming.
- Keyboard-first Textual dashboard.
- Overview, controllers, power-flow, history and event views.
- Persistent incident and evidence view.
- Predictive solar/charge forecast and calibration view.
- Historical investigation/time-travel view.
- Multi-site NOC, low-bandwidth and alert-only modes.
- Plain text/JSON snapshot output.
- Async state locking, reconnect/backoff, tests and CI.
