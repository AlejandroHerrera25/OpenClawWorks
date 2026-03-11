# OpenClaw Operations Center v2
## Arquitectura recomendada por emergent.sh

### Problemas identificados en v1:
1. **I/O síncrono repetitivo** - Cada request lee archivos desde cero
2. **Sin capa de caché real** - El "caché" actual es por instancia (muere con cada request)
3. **APIs bloqueantes** - BaseHTTPRequestHandler es single-threaded
4. **Búsqueda O(n*m)** - Sin indexación
5. **UI desorganizada** - CSS/HTML no responsivo

### Nueva arquitectura:
```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React/UI)                                            │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│ │ Overview │ │ Watchdog │ │ Skills   │ │ Logs     │          │
│ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │ WebSocket + REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ FastAPI Gateway (async)                                         │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│ │ REST Routes │ │ WebSocket   │ │ Search      │                │
│ │ /api/*      │ │ /ws/live    │ │ /api/search │                │
│ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ DataManager (Singleton)                                         │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ In-Memory State Store                                      ││
│ │ events: List[Event] │ sessions: Dict │ skills: Dict       ││
│ └─────────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ SQLite FTS5 (Search Index)                                 ││
│ │ CREATE VIRTUAL TABLE search_idx USING fts5(...)            ││
│ └─────────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ FileWatcher (watchdog library)                             ││
│ │ on_modified → update_state() → broadcast_ws()              ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
   .system_events/   .watchdog/        skills/
```

### Resultados esperados:
- **First Load**: <200ms (vs 1500ms actual)
- **Subsequent Loads**: <50ms (vs 800-2000ms actual)
- **Search**: <100ms con FTS5 (vs 2000ms+ actual)
- **Concurrent Users**: 50+ (vs 3 max actual)
- **Error Rate**: <1% (vs 30% actual)