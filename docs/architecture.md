# Architecture

MorningstarModbusFrontendCLI is a read-only client of MorningstarModbusAPI. It deliberately contains no Modbus stack, serial probing, controller identity logic, database access, or controller write operations.

## Data flow

```text
Morningstar controllers
        │
        ▼
MorningstarModbusAPI
   │ REST      │ SSE
   └──────┬────┘
          ▼
MorningstarAPIClient (httpx.AsyncClient)
          │
          ▼
DashboardRuntime
  ├─ per-site REST refresh task
  ├─ per-site SSE task
  ├─ reconnect/backoff
  ├─ history queries
  ├─ investigation queries
  ├─ bounded controller enrichment
  └─ fleet hydration
          │
          ▼
StateStore (asyncio.Lock)
  ├─ SiteState
  └─ controller_integrity cache
          │
          ▼
Textual views / plain snapshot output
```

All network access is asynchronous. Concurrent writers update the shared state only through `StateStore`, which protects mutable snapshots with `asyncio.Lock`. No synchronous network client is used.

## API authority

The frontend renders the API's evidence and semantics instead of duplicating them. In particular:

- physical identity is `controller_uid`;
- system power and energy use the API's normalized/quality-aware resources;
- incidents and health scores are rendered as returned by the site-intelligence service;
- forecasts display the API's uncertainty bands/confidence instead of creating a second predictor;
- historical views request the API's bounded resolutions, allowing Storage v2 to select efficient storage tiers internally.

## Multi-site v0.5 runtime

Each `[[sites]]` entry receives its own `MorningstarAPIClient` and site worker. A worker performs an initial REST hydration, opens the system SSE stream, and keeps a slower REST refresh loop for resources that are not emitted continuously. Stream failure cancels the paired refresh task, marks the stream degraded, and enters bounded exponential reconnect.

`--low-bandwidth` raises the REST interval to at least 60 seconds while keeping SSE. `--alert-only` avoids the continuous stream and relies on periodic intelligence refreshes, which is intended for constrained links where second-by-second telemetry is not required.

## Investigation mode

The API persists telemetry and events, but not every historical derived screen state. v0.4 therefore does not fabricate historical health. It queries a bounded window around a UTC cursor for important normalized metrics and correlates the returned event timeline. The cursor can move in five-minute or one-hour increments.

## Controller integrity v0.6

Controller-scoped reconciliation resources are loaded on demand rather than added to the continuous site refresh loop. `DashboardRuntime.fetch_controller_integrity()` fetches controller detail, live telemetry, health/charge intelligence, 90-day coverage/gaps/retained-history evidence, and 30/90-day energy summaries concurrently.

A short-lived controller cache makes repeated navigation inexpensive. Fleet hydration is bounded by an `asyncio.Semaphore`, and individual controller cache entries are written atomically under `StateStore`'s existing `asyncio.Lock` so concurrent enrichment requests cannot overwrite one another.

The frontend does not reinterpret controller-retained daily evidence as synthetic high-frequency samples. Coverage, gap status and energy discrepancy semantics remain authoritative in MorningstarModbusAPI.

## Operator workflow v0.7

The Textual shell retains the existing numbered global views while adding a navigation stack, contextual controller drill-down and a searchable command palette. The subtitle provides a lightweight site/system/view breadcrumb. These are presentation/navigation primitives only; they do not move controller or analytics authority into the frontend.

## Fleet analytics v0.8

Fleet comparison asynchronously hydrates the configured sites' physical controllers and aggregates already-authoritative controller evidence into comparison tables. It compares 90-day evidence coverage and 30/90-day energy totals/discrepancy without creating a second forecasting, reconciliation or energy-accounting engine.
