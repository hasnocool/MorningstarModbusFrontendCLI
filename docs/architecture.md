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
  ├─ lazy controller diagnostics
  ├─ lazy site-details hydration
  └─ fleet hydration
          │
          ▼
StateStore (asyncio.Lock)
  ├─ SiteState
  ├─ SiteDetailsBundle cache
  └─ controller_integrity cache
          │
          ▼
Textual operator workspaces / plain snapshot output
```

All network access is asynchronous. Concurrent writers update the shared state only through `StateStore`, which protects mutable snapshots with `asyncio.Lock`. No synchronous network client is used.

## API authority

The frontend renders the API's evidence and semantics instead of duplicating them. In particular:

- physical identity is `controller_uid`;
- system power and energy use the API's normalized/quality-aware resources;
- incidents and health scores are rendered as returned by the site-intelligence service;
- forecasts display the API's uncertainty bands/confidence instead of creating a second predictor;
- historical views request the API's bounded resolutions, allowing Storage v2 to select efficient storage tiers internally;
- topology/component relationships retain API-provided confidence and evidence rather than inferring wiring from transport proximity in the frontend;
- controller-retained records, polling history, samples and energy reconciliation remain distinct provenance classes.

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

## Expanded information architecture v0.9

v0.9 separates the application into four operator contexts instead of continually expanding a flat screen list:

```text
SYSTEM      overview / system details / power / incidents / forecast
CONTROLLER  inventory / live telemetry / data integrity / diagnostics
HISTORY     history / events / investigation
SITE/FLEET  topology / NOC / fleet analytics
```

The navigation bar and command palette use the same taxonomy. Existing `1`–`9` shortcuts remain valid, while contextual letter shortcuts open the detailed workspaces.

### Site-details cache

System metric catalog, component graph, components, relationships, system energy and topology are useful but do not need to be fetched every 15 seconds. `DashboardRuntime.fetch_site_details()` therefore hydrates them only when System Details, Topology or the expanded Power workspace requests them.

The data is stored in `SiteDetailsBundle` with a short-lived cache and a dedicated bounded `asyncio.Semaphore`. Refreshing one of those workspaces can force a new hydration without altering the background SSE/REST cadence.

### Controller diagnostics cache

Fleet hydration deliberately stays cheaper than full diagnostics. `fetch_controller_integrity()` contains the evidence required by inventory/data-integrity/fleet views. `fetch_controller_diagnostics()` adds the heavier controller history summary, polling performance/history, controller incidents and recent samples only when the Diagnostics workspace is opened.

It enriches the existing immutable-style bundle using `dataclasses.replace()` and writes the resulting cache entry atomically through `StateStore`.

### Generic payload explorer

MorningstarModbusAPI evolves as additional source-backed registers and normalized fields are added. The v0.9 telemetry/system/diagnostics workspaces use defensive JSON flattening helpers that expose nested scalar values together with available units, quality and source/provenance metadata.

This is intentionally a rendering mechanism, not a semantic engine. It lets new backend data become visible without requiring the TUI to invent or duplicate register meanings.

### Performance boundary

The normal periodic site worker remains focused on the information required for live operation: system summary, latest normalized telemetry, controller inventory, power flow, energy ledger, health, events and site intelligence. Expensive detail surfaces remain on-demand. This preserves low-bandwidth/alert-only behavior and prevents the expanded TUI from turning richer visibility into continuous network or database load.
