# Architecture

MorningstarModbusFrontendCLI remains an API-only, read-only client of MorningstarModbusAPI.

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
  ├─ per-site REST refresh
  ├─ per-site SSE stream
  ├─ bounded controller enrichment (Semaphore)
  ├─ history / investigation
  └─ fleet hydration
          │
          ▼
StateStore (asyncio.Lock)
  ├─ SiteState
  └─ controller_integrity cache
          │
          ▼
Textual views
```

All network operations are asynchronous. Controller analytics are loaded on demand and cached briefly. Individual controller cache entries are written atomically under `StateStore`'s `asyncio.Lock`, preventing concurrent fleet requests from overwriting each other.

The frontend does not reinterpret controller-retained daily evidence as synthetic high-frequency samples. Coverage, gap status and energy discrepancy semantics remain authoritative in MorningstarModbusAPI.
