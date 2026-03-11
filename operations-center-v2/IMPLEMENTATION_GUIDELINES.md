# 📘 DOCTRINA DE IMPLEMENTACIÓN
## OpenClaw Operations Center v2

> **Documento de referencia obligatorio** para cualquier desarrollo, modificación o extensión del proyecto.
> 
> **Objetivo:** Software que un **equipo de ingeniería senior mantendría en producción.**

---

## 🎯 MISIÓN PRINCIPAL

Entregar soluciones fullstack que sean:

| Atributo | Descripción |
|----------|-------------|
| **Funcional** | Código que ejecuta, no que simula |
| **Seguro** | Input siempre validado, secrets en env vars |
| **Tipado** | Type safety en frontend y backend |
| **Accesible** | A11y no es opcional |
| **Performante** | Sin re-renders innecesarios, bundles livianos |
| **Mantenible** | Código que otros pueden entender y modificar |
| **Auditable** | Logging claro, errores trazables |
| **Production-ready** | Sin TODOs críticos, sin mocks como producción |

### ⛔ PROHIBICIONES ABSOLUTAS
- **Nunca** simular capacidades de backend
- **Nunca** fabricar integraciones o APIs
- **Nunca** presentar datos mock como datos de producción
- **Nunca** implicar comportamiento que no está implementado

---

## 📐 DOCTRINA ARQUITECTÓNICA

### Los 7 Principios Fundamentales

```
1. CORRECTNESS OVER CLEVERNESS
   → Código que funciona > código "elegante" que falla

2. EXPLICITNESS OVER MAGIC
   → Comportamiento predecible > abstracciones ocultas

3. MINIMAL COMPLEXITY
   → Resolver el problema, no demostrar habilidad

4. ACCESSIBILITY BY DEFAULT
   → A11y desde el diseño, no como parche

5. SECURITY BY DESIGN
   → Todo input es hostil hasta probar lo contrario

6. TYPE SAFETY EVERYWHERE
   → Si no está tipado, no está terminado

7. MAINTAINABILITY OVER NOVELTY
   → Código aburrido que funciona > código innovador que nadie entiende
```

### Estructura del Proyecto
```
operations-center-v2/
├── app/
│   ├── api/           # Endpoints y rutas (FastAPI)
│   │   └── main.py    # Gateway principal - SOLO routing
│   ├── core/          # Lógica de negocio
│   │   └── data_manager.py  # Singleton de datos
│   ├── routers/       # Rutas específicas por dominio
│   ├── services/      # Lógica de negocio aislada
│   ├── schemas/       # Pydantic models (request/response)
│   └── models/        # Modelos de dominio
├── ui/                # Frontend (HTML/CSS/JS)
│   └── overview.html  # Dashboard principal
├── logs/              # Logs del servidor (generados)
└── tests/             # Tests unitarios e integración
```

### Diagrama de Arquitectura
```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (UI)                            │
│         HTML Semántico + CSS Variables + Vanilla JS         │
│         Estados: loading | empty | success | error          │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST + WebSocket
                          │ Contratos tipados
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Gateway (async)                     │
│  /api/* endpoints  │  /ws/live WebSocket  │  /ui/* static  │
│  Request Model → Validation → Response Model                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              DataManager (Singleton)                        │
│  • In-Memory State    • Cache con TTL    • FileWatcher     │
│  • SQLite FTS5 Search Index                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐍 BACKEND (Python/FastAPI)

### Estructura de Archivos Backend

```
app/
├── api/
│   └── main.py          # Solo setup de app y routers
├── routers/
│   ├── events.py        # /api/events/*
│   ├── watchdog.py      # /api/watchdog/*
│   └── search.py        # /api/search/*
├── services/
│   ├── event_service.py # Lógica de eventos
│   └── search_service.py
├── schemas/
│   ├── requests.py      # Request models
│   └── responses.py     # Response models
└── core/
    ├── config.py        # Settings centralizados
    └── data_manager.py  # Singleton
```

### Contratos de API (OBLIGATORIO)

Todo endpoint **DEBE** tener:
- Request model (Pydantic)
- Response model (Pydantic)
- Reglas de validación explícitas

```python
# ✅ CORRECTO: Contrato completo y explícito
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class SeverityLevel(str, Enum):
    S1 = "S1"  # Critical
    S2 = "S2"  # High
    S3 = "S3"  # Medium
    S4 = "S4"  # Low

# Request Schema
class EventsQueryParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200, description="Max events to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    severity: Optional[SeverityLevel] = Field(None, description="Filter by severity")

# Response Schema
class EventItem(BaseModel):
    id: str
    type: str
    severity: SeverityLevel
    timestamp: str
    source: str

class EventsResponse(BaseModel):
    success: bool = True
    data: List[EventItem]
    total: int
    filters_applied: dict

# Endpoint con tipos explícitos
@router.get("/events", response_model=EventsResponse)
async def get_events(params: EventsQueryParams = Depends()):
    """Retorna eventos paginados con filtros opcionales."""
    events = event_service.get_events(
        limit=params.limit,
        offset=params.offset,
        severity=params.severity
    )
    return EventsResponse(
        data=events,
        total=len(events),
        filters_applied={"severity": params.severity}
    )

# ❌ INCORRECTO: Payload impredecible
@app.get("/events")
async def get_events():
    return {"data": some_data}  # Sin tipado, sin validación
```

### Parámetros de Query en FastAPI

```python
# ✅ CORRECTO: Usar 'pattern' para validación regex (FastAPI v2+)
from fastapi import Query

@app.get("/api/events")
async def get_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    severity: Optional[str] = Query(None, pattern="^(S1|S2|S3|S4)$")
):
    pass

# ❌ INCORRECTO: 'regex' está DEPRECADO en Pydantic v2
severity: Optional[str] = Query(None, regex="^(S1|S2|S3|S4)$")  # NO USAR
```

### Funciones vs Métodos de Clase

```python
# ✅ CORRECTO: Función independiente SIN 'self'
def _group_results_by_type(results: List[Dict]) -> Dict[str, int]:
    """Agrupa resultados por tipo."""
    types: Dict[str, int] = {}
    for result in results:
        result_type = result.get("type", "unknown")
        types[result_type] = types.get(result_type, 0) + 1
    return types

# Llamada correcta:
grouped = _group_results_by_type(results)

# ❌ INCORRECTO: Usar 'self' fuera de una clase
def _group_results_by_type(self, results):  # ERROR FATAL
    pass
```

### Manejo de Fechas y Timezone

```python
# ✅ CORRECTO: Siempre timezone aware
from datetime import datetime, timezone

def get_current_time() -> datetime:
    """Retorna tiempo actual con timezone UTC."""
    return datetime.now(timezone.utc)

def parse_iso_date(iso_string: str) -> datetime:
    """Parsea fecha ISO con manejo de timezone."""
    parsed = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return parsed

def calculate_age_days(iso_string: str) -> int:
    """Calcula días desde una fecha ISO."""
    parsed = parse_iso_date(iso_string)
    now = datetime.now(timezone.utc) if parsed.tzinfo else datetime.now()
    return (now - parsed).days

# ❌ INCORRECTO: datetime naive
datetime.now()      # Sin timezone - comparaciones incorrectas
datetime.utcnow()   # DEPRECADO en Python 3.12+
```

### Manejo de Excepciones (Crítico)

```python
# ✅ CORRECTO: Excepciones específicas con logging
import logging
logger = logging.getLogger(__name__)

def process_event(data: dict) -> Optional[Event]:
    try:
        return Event(**data)
    except ValidationError as e:
        logger.warning(f"Invalid event data: {e}")
        return None
    except (KeyError, TypeError) as e:
        logger.error(f"Event processing failed: {e}")
        raise EventProcessingError(f"Cannot process event: {e}")

# ✅ CORRECTO: Múltiples excepciones conocidas
try:
    result = risky_operation()
except (ValueError, TypeError, AttributeError) as e:
    logger.warning(f"Operation failed: {e}")
    return fallback_value
except Exception as e:
    logger.exception(f"Unexpected error: {e}")  # Con stack trace
    raise

# ❌ INCORRECTO: Bare except (captura Ctrl+C, SystemExit)
try:
    process()
except:  # NUNCA
    pass

# ❌ INCORRECTO: Exception silenciada
except Exception:
    return None  # ¿Qué falló? Imposible saber
```

### Seguridad Backend

```python
# ✅ CORRECTO: Validación de input
from pydantic import BaseModel, validator, Field
import re

class SearchQuery(BaseModel):
    q: str = Field(..., min_length=2, max_length=100)
    
    @validator('q')
    def sanitize_query(cls, v):
        # Remover caracteres peligrosos para FTS5
        return re.sub(r'[^\w\s\-]', '', v)

# ✅ CORRECTO: No exponer errores en producción
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    is_prod = os.environ.get("ENV") == "production"
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "internal_error",
            "message": "An error occurred" if is_prod else str(exc)
        }
    )

# ❌ INCORRECTO: Exponer stack traces
"message": str(exc),
"traceback": traceback.format_exc()  # NUNCA en producción

# ❌ INCORRECTO: Confiar en datos del cliente
user_role = request.headers.get("X-User-Role")  # Fácilmente falsificable
if user_role == "admin":
    do_admin_stuff()  # VULNERABLE
```

### CORS y Configuración

```python
# ✅ CORRECTO: CORS configurable por entorno
from pydantic import BaseSettings

class Settings(BaseSettings):
    env: str = "development"
    allowed_origins: str = "http://localhost:8000"
    
    @property
    def cors_origins(self) -> List[str]:
        return self.allowed_origins.split(",")
    
    class Config:
        env_file = ".env"

settings = Settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ⚠️ SOLO DESARROLLO: allow_origins=["*"]
# ❌ PRODUCCIÓN: NUNCA usar ["*"]
```

---

## 🌐 FRONTEND (HTML/CSS/JavaScript)

### Estados de UI (OBLIGATORIOS)

Todo componente que carga datos **DEBE** manejar 4 estados:

```javascript
// ✅ CORRECTO: Estados explícitos
const UIState = {
    LOADING: 'loading',
    EMPTY: 'empty',
    SUCCESS: 'success',
    ERROR: 'error'
};

let currentState = UIState.LOADING;

function renderComponent(state, data, error) {
    switch(state) {
        case UIState.LOADING:
            return renderSkeleton();
        case UIState.EMPTY:
            return renderEmptyState("No data available");
        case UIState.SUCCESS:
            return renderData(data);
        case UIState.ERROR:
            return renderError(error);
    }
}

// ❌ INCORRECTO: Solo manejar caso feliz
function render(data) {
    return data.map(item => renderItem(item));  // ¿Y si es null? ¿Error?
}
```

### URLs de API

```javascript
// ✅ CORRECTO: URL dinámica basada en el origen
const API_BASE = window.location.origin + '/api';
// O simplemente:
const API_BASE = '/api';

// ❌ INCORRECTO: URL hardcodeada - FALLA en producción
const API_BASE = 'http://localhost:8000/api';  // NUNCA
```

### Fetch con Manejo de Errores Completo

```javascript
// ✅ CORRECTO: Manejo exhaustivo de errores
async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        
        // HTTP errors
        if (!response.ok) {
            if (response.status >= 500) {
                throw new APIError('Server error', response.status);
            } else if (response.status === 404) {
                throw new APIError('Not found', response.status);
            } else if (response.status === 401) {
                throw new APIError('Unauthorized', response.status);
            } else {
                throw new APIError(`HTTP ${response.status}`, response.status);
            }
        }
        
        const data = await response.json();
        
        // API-level errors
        if (!data.success) {
            throw new APIError(data.message || 'API error', response.status);
        }
        
        return data.data;
        
    } catch (error) {
        // Network errors
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
            throw new NetworkError('Server unreachable');
        }
        throw error;
    }
}

// Custom error classes
class APIError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }
}

class NetworkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'NetworkError';
    }
}
```

### Try/Catch con Logging

```javascript
// ✅ CORRECTO: catch con variable y logging
try {
    const date = new Date(timestamp);
    return formatDate(date);
} catch (e) {
    console.warn('Date parsing error:', e.message, { timestamp });
    return '--';
}

// ❌ INCORRECTO: catch vacío
} catch {
    return '--';  // Imposible debuggear
}
```

### HTML Semántico y Accesibilidad

```html
<!-- ✅ CORRECTO: HTML semántico con a11y -->
<nav aria-label="Main navigation">
    <ul role="menubar">
        <li role="none">
            <a href="#overview" role="menuitem" class="nav-tab active">
                Overview
            </a>
        </li>
    </ul>
</nav>

<main id="main-content">
    <section aria-labelledby="overview-title">
        <h2 id="overview-title">System Overview</h2>
        
        <!-- Form inputs con labels -->
        <label for="search-input">Search</label>
        <input 
            type="search" 
            id="search-input" 
            name="search"
            aria-describedby="search-help"
        >
        <span id="search-help" class="sr-only">
            Search events, skills, and sessions
        </span>
        
        <!-- Botones reales -->
        <button type="button" onclick="refresh()">
            Refresh Data
        </button>
    </section>
</main>

<!-- ❌ INCORRECTO: Div como botón -->
<div class="button" onclick="doSomething()">Click me</div>

<!-- ❌ INCORRECTO: Input sin label -->
<input type="text" placeholder="Search...">

<!-- ❌ INCORRECTO: Link sin href real -->
<a onclick="navigate()">Go somewhere</a>
```

### CSS Variables y Sistema de Diseño

```css
/* ✅ CORRECTO: Sistema de diseño con tokens */
:root {
    /* Colors - Semantic naming */
    --color-bg-primary: #0a0a0f;
    --color-bg-surface: #12121a;
    --color-bg-elevated: #1a1a24;
    
    --color-text-primary: #e0e0e0;
    --color-text-secondary: #888888;
    --color-text-disabled: #555555;
    
    --color-border-default: #2a2a3a;
    --color-border-hover: #3a3a4a;
    
    --color-accent-primary: #6366f1;
    --color-accent-hover: #7c7ff2;
    
    --color-status-success: #22c55e;
    --color-status-warning: #f59e0b;
    --color-status-error: #ef4444;
    --color-status-info: #3b82f6;
    
    /* Spacing - 4px base unit */
    --space-1: 0.25rem;  /* 4px */
    --space-2: 0.5rem;   /* 8px */
    --space-3: 0.75rem;  /* 12px */
    --space-4: 1rem;     /* 16px */
    --space-6: 1.5rem;   /* 24px */
    --space-8: 2rem;     /* 32px */
    
    /* Typography */
    --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-family-mono: 'SF Mono', Consolas, monospace;
    
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    
    /* Borders */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-full: 9999px;
    
    /* Shadows */
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.15);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.2);
    
    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-base: 250ms ease;
    --transition-slow: 350ms ease;
    
    /* Z-index scale */
    --z-dropdown: 100;
    --z-modal: 200;
    --z-toast: 300;
}

/* Componente usando tokens */
.card {
    background: var(--color-bg-surface);
    border: 1px solid var(--color-border-default);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    transition: border-color var(--transition-fast);
}

.card:hover {
    border-color: var(--color-border-hover);
}

/* ❌ INCORRECTO: Valores hardcodeados */
.card {
    background: #12121a;  /* ¿Qué color es? */
    padding: 16px;        /* ¿Por qué 16? */
    border-radius: 8px;   /* Inconsistente */
}
```

### Responsive Design (Mobile-First)

```css
/* ✅ CORRECTO: Mobile-first */
.grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--space-4);
}

/* Tablet */
@media (min-width: 768px) {
    .grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop */
@media (min-width: 1024px) {
    .grid {
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    }
}

/* ❌ INCORRECTO: Desktop-first */
.grid {
    grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 1024px) {
    .grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
```

### Performance Frontend

```javascript
// ✅ CORRECTO: Lazy loading y memoización cuando justificado
const cache = new Map();

async function fetchWithCache(endpoint, ttl = 30000) {
    const cacheKey = endpoint;
    const cached = cache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < ttl) {
        return cached.data;
    }
    
    const data = await fetchData(endpoint);
    cache.set(cacheKey, { data, timestamp: Date.now() });
    return data;
}

// ✅ CORRECTO: Debounce para inputs frecuentes
function debounce(fn, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
}

const debouncedSearch = debounce(async (query) => {
    const results = await fetchData(`/search?q=${query}`);
    renderResults(results);
}, 300);

// ❌ INCORRECTO: Llamada en cada keystroke
input.addEventListener('keyup', async (e) => {
    const results = await fetchData(`/search?q=${e.target.value}`);
    renderResults(results);  // API bombardeada
});
```

---

## 🗄️ DATA MANAGER (Singleton)

### Implementación Thread-Safe

```python
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import threading

@dataclass
class CacheEntry:
    """Entrada de caché con TTL."""
    data: Any
    timestamp: datetime
    ttl_seconds: int = 30
    
    @property
    def is_valid(self) -> bool:
        elapsed = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return elapsed < self.ttl_seconds

class DataManager:
    """
    Singleton thread-safe para gestión de estado en memoria.
    
    Responsabilidades:
    - Cargar datos desde filesystem
    - Mantener caché con TTL
    - Proveer búsqueda FTS5
    - Notificar cambios via FileWatcher
    """
    
    _instance: Optional['DataManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'DataManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check locking
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._cache: Dict[str, CacheEntry] = {}
        self._db_lock = threading.Lock()
        self._subscribers: List[Callable] = []
        
        self._init_database()
        self._init_file_watcher()
        self._load_initial_data()
        
        self._initialized = True
    
    def get_cached(
        self, 
        key: str, 
        loader: Callable[[], Any], 
        ttl: int = 30
    ) -> Any:
        """
        Obtiene dato de caché o lo carga si expiró.
        
        Args:
            key: Identificador único del caché
            loader: Función que carga los datos
            ttl: Tiempo de vida en segundos
            
        Returns:
            Datos cacheados o recién cargados
        """
        if key in self._cache and self._cache[key].is_valid:
            return self._cache[key].data
        
        data = loader()
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=datetime.now(timezone.utc),
            ttl_seconds=ttl
        )
        return data
```

### SQLite con Thread Safety

```python
import sqlite3

def _init_database(self) -> None:
    """Inicializa SQLite con FTS5 para búsqueda."""
    self._db = sqlite3.connect(
        "/tmp/operations_search.db",
        check_same_thread=False  # Requiere uso de _db_lock
    )
    
    with self._db_lock:
        self._db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS search_index 
            USING fts5(id, type, content, metadata, timestamp)
        """)
        self._db.commit()

def search(self, query: str, limit: int = 50) -> List[Dict]:
    """
    Búsqueda FTS5 - O(log n) vs O(n*m) de búsqueda lineal.
    
    IMPORTANTE: Siempre usar _db_lock para operaciones de DB.
    """
    if not query or len(query) < 2:
        return []
    
    with self._db_lock:  # CRÍTICO: Lock obligatorio
        cursor = self._db.execute("""
            SELECT id, type, content, bm25(search_index) as rank
            FROM search_index
            WHERE search_index MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        return [
            {"id": row[0], "type": row[1], "content": row[2], "score": abs(row[3])}
            for row in cursor
        ]
```

---

## ✅ CHECKLIST PRE-COMMIT

### Backend
- [ ] Todos los endpoints tienen request/response models (Pydantic)
- [ ] No hay `regex=` en Query parameters (usar `pattern=`)
- [ ] No hay funciones con `self` fuera de clases
- [ ] No hay `except:` sin tipo de excepción
- [ ] Todas las fechas usan `timezone.utc`
- [ ] Los errores se loggean antes de silenciarse
- [ ] CORS restringido para producción
- [ ] No hay secrets hardcodeados
- [ ] Input validado y sanitizado

### Frontend
- [ ] `API_BASE` usa URL relativa o `window.location.origin`
- [ ] Todos los `catch` tienen variable de error
- [ ] Los 4 estados de UI están implementados (loading/empty/success/error)
- [ ] HTML es semántico (button, a, label, etc.)
- [ ] Inputs tienen labels asociados
- [ ] Focus states visibles
- [ ] CSS usa variables del sistema de diseño
- [ ] Responsive funciona en móvil

### General
- [ ] No hay `console.log` en producción
- [ ] No hay TODOs críticos sin resolver
- [ ] No hay datos mock presentados como producción
- [ ] Variables de entorno documentadas

---

## 🚨 ANTI-PATRONES (PROHIBIDOS)

| Anti-Patrón | Por qué es malo | Alternativa |
|-------------|-----------------|-------------|
| URLs hardcodeadas | Falla en producción | `window.location.origin` |
| `except:` sin tipo | Captura Ctrl+C | `except SpecificError` |
| `datetime.now()` sin tz | Comparaciones incorrectas | `datetime.now(timezone.utc)` |
| `self` fuera de clase | TypeError en runtime | Función sin `self` |
| CORS `["*"]` en prod | Vulnerabilidad XSS | Lista de dominios |
| Secrets en código | Exposición de credenciales | Variables de entorno |
| `any` en TypeScript | Pierde type safety | Tipos específicos |
| Div como botón | Inaccesible | `<button>` real |
| CSS valores repetidos | Inconsistencia | CSS variables |
| Errores silenciados | Imposible debuggear | Logging antes de ignorar |
| Mock como producción | Engaña al usuario | Marcar claramente |
| API sin response model | Payload impredecible | Pydantic models |

---

## 📋 CONVENCIONES DE NAMING

| Tipo | Convención | Ejemplo |
|------|------------|---------|
| Archivos Python | snake_case | `data_manager.py` |
| Clases | PascalCase | `DataManager` |
| Funciones/métodos | snake_case | `get_overview()` |
| Constantes | UPPER_SNAKE | `MAX_EVENTS = 1000` |
| Variables privadas | _prefijo | `_cache`, `_db_lock` |
| Pydantic models | PascalCase | `EventResponse` |
| Endpoints API | kebab-case | `/api/health-check` |
| Query params | snake_case | `?page_size=10` |
| CSS classes | kebab-case | `.metric-card` |
| CSS variables | --kebab-case | `--color-accent` |
| JS variables | camelCase | `dataCache` |
| JS constantes | UPPER_SNAKE | `API_BASE` |

---

## 🔧 VARIABLES DE ENTORNO

### Requeridas
```bash
ENV=development|production
```

### Opcionales
```bash
ALLOWED_ORIGINS=http://localhost:8000,https://midominio.com
LOG_LEVEL=debug|info|warning|error
DATABASE_PATH=/tmp/operations.db
```

### Uso en Código
```python
# ✅ CORRECTO: Settings centralizados con Pydantic
from pydantic import BaseSettings

class Settings(BaseSettings):
    env: str = "development"
    log_level: str = "info"
    allowed_origins: str = "http://localhost:8000"
    
    @property
    def is_production(self) -> bool:
        return self.env == "production"
    
    class Config:
        env_file = ".env"

settings = Settings()

# ❌ INCORRECTO: os.environ directo sin defaults
env = os.environ.get("ENV")  # Puede ser None
```

---

## ⚠️ GESTIÓN DE SERVIDORES Y PUERTOS (CRÍTICO)

### El Problema Común
Los agentes frecuentemente caen en loops infinitos intentando:
- Matar procesos que no mueren
- Iniciar servidores en puertos ocupados
- Modificar código para cambiar puertos cuando el problema es un proceso zombie

### Regla #1: NUNCA Hardcodear Puertos

```python
# ❌ INCORRECTO: Puerto hardcodeado
PORT = 8000  # Si está ocupado, el agente entra en loop

def run_server():
    # No hay forma de cambiar el puerto sin modificar código
    with socketserver.TCPServer(("", 8000), Handler) as httpd:
        httpd.serve_forever()

# ✅ CORRECTO: Puerto configurable via variable de entorno
import os

PORT = int(os.environ.get("PORT", 8000))

def run_server(port: int = None):
    """
    Inicia el servidor en el puerto especificado.
    
    Args:
        port: Puerto a usar. Si es None, usa PORT del entorno.
    """
    server_port = port or PORT
    
    with socketserver.TCPServer(("", server_port), Handler) as httpd:
        print(f"Server running on port {server_port}")
        httpd.serve_forever()

# Llamada con puerto personalizado:
run_server(port=8001)  # Fácil cambiar sin modificar código
```

### Regla #2: Script de Inicio con Cleanup Automático

```bash
#!/bin/bash
# start.sh - SIEMPRE incluir cleanup antes de iniciar

set -e

PORT=${PORT:-8000}

echo "🧹 Limpiando procesos anteriores en puerto $PORT..."

# Método 1: Matar por puerto (más confiable)
fuser -k ${PORT}/tcp 2>/dev/null || true

# Método 2: Matar por nombre de proceso (backup)
pkill -f "python.*server" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# Esperar a que el puerto se libere
sleep 2

# Verificar que el puerto está libre
if lsof -i :${PORT} > /dev/null 2>&1; then
    echo "❌ ERROR: Puerto $PORT sigue ocupado"
    lsof -i :${PORT}
    exit 1
fi

echo "✅ Puerto $PORT libre, iniciando servidor..."

# Iniciar servidor
python -m uvicorn app.api.main:app --host 0.0.0.0 --port $PORT
```

### Regla #3: Verificar Puerto ANTES de Intentar Usarlo

```python
import socket

def is_port_available(port: int) -> bool:
    """Verifica si un puerto está disponible."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return True
        except OSError:
            return False

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Encuentra el primer puerto disponible."""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")

# Uso en servidor
def run_server():
    port = int(os.environ.get("PORT", 8000))
    
    if not is_port_available(port):
        print(f"⚠️ Puerto {port} ocupado, buscando alternativa...")
        port = find_available_port(port + 1)
        print(f"✅ Usando puerto alternativo: {port}")
    
    # Iniciar servidor en puerto disponible
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Regla #4: Funciones Deben Aceptar Parámetros de Configuración

```python
# ❌ INCORRECTO: Función sin parámetros - imposible reconfigurar
def run_server():
    PORT = 8000  # Hardcodeado dentro de la función
    httpd = HTTPServer(("", PORT), Handler)
    httpd.serve_forever()

# ✅ CORRECTO: Función con parámetros y defaults sensatos
def run_server(
    host: str = "0.0.0.0",
    port: int = None,
    reload: bool = None
) -> None:
    """
    Inicia el servidor HTTP.
    
    Args:
        host: Host a bindear (default: 0.0.0.0)
        port: Puerto (default: variable PORT o 8000)
        reload: Hot reload (default: True en dev, False en prod)
    """
    server_port = port or int(os.environ.get("PORT", 8000))
    is_dev = os.environ.get("ENV", "development") == "development"
    should_reload = reload if reload is not None else is_dev
    
    print(f"🚀 Starting server on {host}:{server_port}")
    
    uvicorn.run(
        "app.api.main:app",
        host=host,
        port=server_port,
        reload=should_reload
    )

# Ahora el agente puede hacer:
run_server(port=8001)  # Sin modificar código interno
```

### Regla #5: Manejo de Señales para Cleanup Graceful

```python
import signal
import sys

def cleanup_handler(signum, frame):
    """Handler para limpieza al recibir señal de terminación."""
    print("\n🛑 Señal recibida, limpiando...")
    
    # Cerrar conexiones de DB
    if hasattr(data_manager, '_db'):
        data_manager._db.close()
    
    # Detener observers
    if hasattr(data_manager, '_observer'):
        data_manager._observer.stop()
    
    print("✅ Cleanup completado")
    sys.exit(0)

# Registrar handlers al inicio
signal.signal(signal.SIGINT, cleanup_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, cleanup_handler)  # kill
```

### Regla #6: NUNCA Entrar en Loop de Debugging de Puertos

Si el agente detecta "Address already in use":

```
✅ HACER:
1. Ejecutar: fuser -k {PORT}/tcp
2. Esperar 2 segundos
3. Verificar con: lsof -i :{PORT}
4. Si sigue ocupado, usar puerto alternativo

❌ NO HACER:
1. Intentar matar el mismo proceso 5 veces
2. Modificar el código para cambiar el puerto
3. Buscar PIDs manualmente con ps aux | grep
4. Reiniciar todo el sistema
```

### Comandos de Diagnóstico Rápido

```bash
# Ver qué proceso usa un puerto
lsof -i :8000

# Matar proceso por puerto (más confiable)
fuser -k 8000/tcp

# Ver todos los puertos en uso
netstat -tlnp | grep LISTEN

# Matar todos los procesos Python de servidor
pkill -9 -f "uvicorn|python.*server"

# Verificar si puerto está libre
nc -z localhost 8000 && echo "Ocupado" || echo "Libre"
```

### Variables de Entorno para Servidores

```bash
# .env
PORT=8000
HOST=0.0.0.0
WORKERS=4
RELOAD=true  # Solo en desarrollo
```

```python
# config.py
from pydantic import BaseSettings

class ServerSettings(BaseSettings):
    port: int = 8000
    host: str = "0.0.0.0"
    workers: int = 4
    reload: bool = False
    
    class Config:
        env_file = ".env"

server_settings = ServerSettings()
```

---

## 🎯 ESTÁNDAR DE CALIDAD

El código final debe parecer trabajo de:
- Un **senior frontend engineer**
- Un **senior backend engineer**
- Un **pragmatic product engineer**

### La Regla de Oro

> **Elige ingeniería sólida sobre espectáculo visual.**
> 
> Código aburrido que funciona > Código innovador que nadie entiende.

---

## 📚 REFERENCIAS

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Migration](https://docs.pydantic.dev/latest/migration/)
- [Python datetime best practices](https://docs.python.org/3/library/datetime.html)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [SQLite threading](https://docs.python.org/3/library/sqlite3.html)

---

**Versión:** 2.0.0  
**Última actualización:** 2025-03-11  
**Basado en:** Fullstack Product Engineer Skill
