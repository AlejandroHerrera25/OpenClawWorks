# 📘 DOCTRINA DE IMPLEMENTACIÓN
## OpenClaw Operations Center v2

> **Documento de referencia obligatorio** para cualquier desarrollo, modificación o extensión del proyecto.

---

## 📐 ARQUITECTURA DEL PROYECTO

### Estructura de Directorios
```
operations-center-v2/
├── app/
│   ├── api/           # Endpoints y rutas (FastAPI)
│   │   └── main.py    # Gateway principal
│   └── core/          # Lógica de negocio
│       └── data_manager.py  # Singleton de datos
├── ui/                # Frontend (HTML/CSS/JS vanilla)
│   └── overview.html  # Dashboard principal
├── logs/              # Logs del servidor (generados)
├── start.sh           # Script de inicio (FastAPI)
└── start_simple.sh    # Script alternativo (HTTP simple)
```

### Patrón de Arquitectura
```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (UI)                            │
│         HTML + CSS Variables + Vanilla JavaScript           │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST + WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Gateway (async)                     │
│     /api/* endpoints  │  /ws/live WebSocket  │  /ui/*      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              DataManager (Singleton)                        │
│  • In-Memory State    • Cache con TTL    • FileWatcher     │
│  • SQLite FTS5 Search Index                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              Sistema de archivos (.openclaw/)
```

---

## 🐍 BACKEND (Python/FastAPI)

### 1. Imports y Dependencias

```python
# ✅ CORRECTO: Imports organizados por tipo
from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone  # SIEMPRE incluir timezone
from pathlib import Path
import asyncio
import json
import os

# ❌ INCORRECTO: Imports desordenados o innecesarios
import json, os, sys  # No mezclar en una línea
from datetime import *  # No usar wildcard imports
```

### 2. Parámetros de Query en FastAPI

```python
# ✅ CORRECTO: Usar 'pattern' para validación regex (FastAPI v2+)
@app.get("/api/events")
async def get_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    severity: Optional[str] = Query(None, pattern="^(S1|S2|S3|S4)$")
):
    pass

# ❌ INCORRECTO: 'regex' está DEPRECADO
severity: Optional[str] = Query(None, regex="^(S1|S2|S3|S4)$")  # NO USAR
```

### 3. Funciones Auxiliares (NO son métodos de clase)

```python
# ✅ CORRECTO: Función independiente SIN 'self'
def _group_results_by_type(results: List[Dict]) -> Dict:
    """Agrupa resultados por tipo"""
    types = {}
    for result in results:
        result_type = result.get("type", "unknown")
        types[result_type] = types.get(result_type, 0) + 1
    return types

# Llamada correcta:
data = _group_results_by_type(results)

# ❌ INCORRECTO: Usar 'self' fuera de una clase
def _group_results_by_type(self, results):  # ERROR: 'self' no aplica
    pass

data = self._group_results_by_type(results)  # ERROR: No existe 'self'
```

### 4. Manejo de Fechas y Timezone

```python
# ✅ CORRECTO: Siempre usar timezone aware
from datetime import datetime, timezone

# Para obtener fecha actual:
now = datetime.now(timezone.utc)

# Para comparar con fechas ISO:
def compare_dates(iso_string: str) -> int:
    parsed = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    
    # Verificar si es aware o naive
    if parsed.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()
    
    return (now - parsed).days

# ❌ INCORRECTO: datetime naive causa errores de comparación
now = datetime.now()  # Sin timezone - EVITAR
datetime.utcnow()     # DEPRECADO en Python 3.12+
```

### 5. Manejo de Excepciones

```python
# ✅ CORRECTO: Especificar tipos de excepción
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    return None
except (ValueError, TypeError) as e:
    print(f"Validation error: {e}")
    return None

# ✅ CORRECTO: Para múltiples excepciones conocidas
except (ValueError, TypeError, AttributeError, KeyError) as e:
    logger.warning(f"Data processing error: {e}")
    return default_value

# ❌ INCORRECTO: Bare except captura TODO (incluso Ctrl+C)
try:
    process_data()
except:  # NO HACER ESTO
    pass

# ❌ INCORRECTO: Capturar Exception sin logging
except Exception:
    return None  # Error silenciado - difícil debugging
```

### 6. WebSocket y Conexiones

```python
# ✅ CORRECTO: Manejo de errores en broadcast
async def broadcast(self, message: dict):
    disconnected = []
    for connection in self.active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"WebSocket send error: {e}")
            disconnected.append(connection)
    
    for conn in disconnected:
        self.disconnect(conn)

# ❌ INCORRECTO: Silenciar errores de WebSocket
except:
    disconnected.append(connection)  # Sin logging - imposible debuggear
```

### 7. Configuración de CORS

```python
# ✅ CORRECTO: CORS configurable por entorno
allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS", 
    "http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ⚠️ SOLO DESARROLLO: allow_origins=["*"]
# ❌ PRODUCCIÓN: Nunca usar ["*"] - vulnerabilidad de seguridad
```

### 8. Exposición de Errores

```python
# ✅ CORRECTO: Ocultar detalles en producción
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    is_production = os.environ.get("ENV") == "production"
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "internal_error",
            "message": "Internal server error" if is_production else str(exc)
        }
    )

# ❌ INCORRECTO: Exponer stack traces al cliente
"message": str(exc)  # En producción revela info sensible
"details": traceback.format_exc()  # NUNCA hacer esto
```

---

## 🌐 FRONTEND (HTML/CSS/JavaScript)

### 1. URLs de API

```javascript
// ✅ CORRECTO: URL dinámica basada en el origen
const API_BASE = window.location.origin + '/api';
// O simplemente:
const API_BASE = '/api';

// ❌ INCORRECTO: URL hardcodeada - NO funciona en producción
const API_BASE = 'http://localhost:8000/api';  // NUNCA
const API_BASE = 'http://127.0.0.1:8000/api';  // NUNCA
```

### 2. Manejo de Errores en Fetch

```javascript
// ✅ CORRECTO: Distinguir tipos de error
async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        
        if (!response.ok) {
            if (response.status >= 500) {
                throw new Error(`Server error: ${response.status}`);
            } else if (response.status === 404) {
                throw new Error(`Endpoint not found: ${endpoint}`);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        }
        
        return await response.json();
    } catch (error) {
        // Distinguir error de red vs error de servidor
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
            throw new Error('Network error: Server unreachable');
        }
        throw error;
    }
}

// ❌ INCORRECTO: Ignorar tipos de error
catch (error) {
    console.log('Error');  // Sin contexto útil
}
```

### 3. Manejo de Try/Catch

```javascript
// ✅ CORRECTO: catch con variable de error
try {
    const date = new Date(timestamp);
    return formatDate(date);
} catch (e) {
    console.warn('Date parsing error:', e);
    return '--';
}

// ❌ INCORRECTO: catch vacío - errores silenciados
} catch {
    return '--';  // ¿Qué falló? Imposible saber
}
```

### 4. CSS Variables y Temas

```css
/* ✅ CORRECTO: Variables centralizadas */
:root {
    --color-bg: #0a0a0f;
    --color-surface: #12121a;
    --color-text: #e0e0e0;
    --color-accent: #6366f1;
    --color-success: #22c55e;
    --color-error: #ef4444;
    
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    
    --radius-md: 8px;
    --transition-fast: 150ms ease;
}

/* Uso consistente */
.card {
    background: var(--color-surface);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
}

/* ❌ INCORRECTO: Valores hardcodeados repetidos */
.card { background: #12121a; padding: 16px; }
.button { background: #12121a; padding: 16px; }
```

### 5. Responsive Design (Mobile-First)

```css
/* ✅ CORRECTO: Base móvil, escalar hacia arriba */
.grid {
    display: grid;
    grid-template-columns: 1fr;  /* Móvil: 1 columna */
    gap: var(--spacing-md);
}

@media (min-width: 768px) {
    .grid {
        grid-template-columns: repeat(2, 1fr);  /* Tablet */
    }
}

@media (min-width: 1024px) {
    .grid {
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    }
}

/* ❌ INCORRECTO: Desktop-first con max-width */
.grid { grid-template-columns: repeat(4, 1fr); }
@media (max-width: 768px) { /* Sobreescribir */ }
```

---

## 🗄️ DATA MANAGER (Singleton)

### Principios del Singleton

```python
# ✅ CORRECTO: Patrón Singleton thread-safe
class DataManager:
    _instance: Optional['DataManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check locking
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return  # Ya inicializado, no repetir
        
        # Inicialización única
        self._load_data()
        self._initialized = True

# Uso global
data_manager = DataManager()
```

### Cache con TTL

```python
# ✅ CORRECTO: Cache con tiempo de expiración
@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl_seconds: int = 30
    
    @property
    def is_valid(self) -> bool:
        elapsed = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return elapsed < self.ttl_seconds

def get_cached(self, key: str, loader: Callable, ttl: int = 30) -> Any:
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

### SQLite Thread Safety

```python
# ✅ CORRECTO: Usar lock para operaciones SQLite
self._db = sqlite3.connect(str(db_path), check_same_thread=False)
self._db_lock = threading.Lock()

def search(self, query: str) -> List[Dict]:
    with self._db_lock:  # SIEMPRE usar el lock
        cursor = self._db.execute("SELECT * FROM search_index WHERE ...")
        return [dict(row) for row in cursor]

# ❌ INCORRECTO: Acceso sin lock
cursor = self._db.execute(...)  # Race condition posible
```

---

## ✅ CHECKLIST PRE-COMMIT

Antes de cada commit, verificar:

### Backend
- [ ] No hay `regex=` en Query parameters (usar `pattern=`)
- [ ] No hay funciones con `self` fuera de clases
- [ ] No hay `except:` sin tipo de excepción
- [ ] Todas las fechas usan `timezone.utc` cuando corresponde
- [ ] Los errores se loggean antes de silenciarse
- [ ] CORS restringido para producción

### Frontend
- [ ] `API_BASE` usa `window.location.origin` o URL relativa
- [ ] Todos los `catch` tienen variable de error (`catch (e)`)
- [ ] Errores de red se distinguen de errores de servidor
- [ ] CSS usa variables (no valores hardcodeados)
- [ ] Responsive funciona en móvil

### General
- [ ] No hay credenciales hardcodeadas
- [ ] No hay console.log en producción (usar condicional)
- [ ] Variables de entorno documentadas

---

## 🔧 VARIABLES DE ENTORNO

### Backend (`backend/.env` o sistema)
```bash
# Requeridas
ENV=development|production

# Opcionales
ALLOWED_ORIGINS=http://localhost:8000,https://midominio.com
LOG_LEVEL=info|warning|error
```

### Uso en código
```python
# ✅ CORRECTO: Con valor por defecto seguro
env = os.environ.get("ENV", "development")
is_prod = env == "production"

# ❌ INCORRECTO: Sin default puede causar None
env = os.environ.get("ENV")  # Puede ser None
if env == "production":  # Falla silenciosamente si None
```

---

## 📋 CONVENCIONES DE NAMING

| Tipo | Convención | Ejemplo |
|------|------------|---------|
| Archivos Python | snake_case | `data_manager.py` |
| Clases | PascalCase | `DataManager` |
| Funciones/métodos | snake_case | `get_overview()` |
| Constantes | UPPER_SNAKE | `MAX_EVENTS = 1000` |
| Variables privadas | _prefijo | `_cache`, `_db_lock` |
| Endpoints API | kebab-case | `/api/health-check` |
| CSS classes | kebab-case | `.metric-card` |
| CSS variables | --kebab-case | `--color-accent` |
| JS variables | camelCase | `dataCache` |
| JS constantes | UPPER_SNAKE | `API_BASE` |

---

## 🚨 ANTI-PATRONES A EVITAR

1. **URLs hardcodeadas** → Usar variables de entorno o detección dinámica
2. **Bare except** → Siempre especificar tipo de excepción
3. **datetime.now() sin timezone** → Usar timezone.utc
4. **self en funciones sueltas** → Solo en métodos de clase
5. **Errores silenciados** → Siempre loggear antes de ignorar
6. **CORS ["*"] en producción** → Restringir a dominios específicos
7. **Secrets en código** → Usar variables de entorno
8. **CSS valores repetidos** → Usar CSS variables
9. **catch sin variable** → Siempre `catch (e)` para debugging

---

## 📚 REFERENCIAS

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Migration](https://docs.pydantic.dev/latest/migration/)
- [Python datetime best practices](https://docs.python.org/3/library/datetime.html)
- [SQLite threading](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect)

---

**Última actualización:** 2025-03-11
**Versión del documento:** 1.0.0
