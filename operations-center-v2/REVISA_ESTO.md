# 🚨 REVISA ESTO - ERRORES CRÍTICOS EN LA UI

> **Para:** Agente de desarrollo  
> **De:** Auditoría de código  
> **Prioridad:** ALTA  
> **Estado actual:** La UI se despliega pero NO es funcional

---

## 📋 RESUMEN DE PROBLEMAS

| # | Problema | Severidad | Sección |
|---|----------|-----------|---------|
| 1 | Recent Events muestra "Unknown event" | 🔴 CRÍTICO | Events |
| 2 | Active Sessions siempre vacío | 🔴 CRÍTICO | Watchdog |
| 3 | Total Events estático (siempre 36) | 🟡 MODERADO | Metrics |
| 4 | Health Score sin explicación | 🟡 MODERADO | Metrics |
| 5 | Skills sin descripción (solo "--") | 🟡 MODERADO | Skills |
| 6 | Tabs de navegación no funcionan | 🔴 CRÍTICO | Navigation |
| 7 | No hay datos reales, solo placeholders | 🔴 CRÍTICO | General |

---

## 🔴 PROBLEMA #1: Recent Events muestra "Unknown event"

### Síntoma
```
Unknown event    Low
46m ago          system
```

### Causa
El frontend espera `event.type` pero el campo viene vacío o no existe en los datos JSON.

### Archivo a corregir
`ui/overview.html` - Línea ~858

### Código actual (INCORRECTO)
```javascript
const html = events.map(event => `
    <li class="event-item">
        <div class="event-header">
            <div class="event-title">${event.type || 'Unknown event'}</div>
            ...
        </div>
    </li>
`).join('');
```

### Código corregido
```javascript
const html = events.map(event => `
    <li class="event-item">
        <div class="event-header">
            <div class="event-title">
                ${event.type || event.event_type || event.name || event.message || 'Event #' + (event.id || 'N/A')}
            </div>
            ...
        </div>
        <div class="event-description">
            ${event.message || event.description || event.details || ''}
        </div>
    </li>
`).join('');
```

### También revisar
`app/core/data_manager.py` - Función `_load_events()` - Verificar qué campos tienen los eventos JSONL:

```python
def _load_events(self):
    """Load events from .system_events/"""
    events = []
    if self.events_dir.exists():
        for event_file in self.events_dir.glob("*.jsonl"):
            try:
                with open(event_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            event = json.loads(line)
                            # DEBUG: Imprimir para ver estructura real
                            print(f"DEBUG Event keys: {event.keys()}")
                            events.append(event)
            except Exception as e:
                print(f"Error loading {event_file}: {e}")
    
    # Ordenar por timestamp
    events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    self._events = events
```

### Acción requerida
1. Agregar `print(event.keys())` para ver qué campos tienen los eventos
2. Ajustar el frontend para usar los campos correctos
3. Si no hay campo `type`, crearlo basado en el nombre del archivo o el contenido

---

## 🔴 PROBLEMA #2: Active Sessions siempre vacío

### Síntoma
```
No active sessions
```

### Causa
El archivo `session_registry.json` no existe o tiene estructura diferente a la esperada.

### Archivo a corregir
`app/core/data_manager.py` - Función `_load_watchdog()`

### Código actual
```python
def _load_watchdog(self):
    session_file = self.watchdog_dir / "session_registry.json"
    if session_file.exists():
        with open(session_file, 'r') as f:
            self._sessions = json.load(f)
```

### Código corregido
```python
def _load_watchdog(self):
    """Load watchdog data with fallback and debugging."""
    self._sessions = {"sessions": []}
    self._metrics = {}
    
    # Buscar archivos de sesión
    session_file = self.watchdog_dir / "session_registry.json"
    
    # DEBUG: Verificar qué archivos existen
    if self.watchdog_dir.exists():
        print(f"DEBUG: Watchdog dir contents: {list(self.watchdog_dir.iterdir())}")
    else:
        print(f"DEBUG: Watchdog dir does NOT exist: {self.watchdog_dir}")
        return
    
    if session_file.exists():
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # DEBUG: Ver estructura
                print(f"DEBUG: Session registry structure: {type(data)}, keys: {data.keys() if isinstance(data, dict) else 'N/A'}")
                
                # Manejar diferentes estructuras posibles
                if isinstance(data, list):
                    self._sessions = {"sessions": data}
                elif isinstance(data, dict):
                    if "sessions" in data:
                        self._sessions = data
                    else:
                        # Convertir dict a lista de sesiones
                        self._sessions = {"sessions": list(data.values())}
        except Exception as e:
            print(f"Error loading sessions: {e}")
    else:
        print(f"DEBUG: Session file not found: {session_file}")
        
        # FALLBACK: Buscar otros archivos JSON en el directorio
        for json_file in self.watchdog_dir.glob("*.json"):
            print(f"DEBUG: Found JSON file: {json_file}")
```

### También en el frontend
`ui/overview.html` - Función `updateWatchdogUI()`

```javascript
function updateWatchdogUI(data) {
    // DEBUG: Ver qué llega
    console.log('Watchdog data:', JSON.stringify(data, null, 2));
    
    // Manejar diferentes estructuras
    let sessions = [];
    
    if (data.sessions) {
        if (Array.isArray(data.sessions)) {
            sessions = data.sessions;
        } else if (data.sessions.sessions) {
            sessions = data.sessions.sessions;
        } else if (typeof data.sessions === 'object') {
            sessions = Object.values(data.sessions);
        }
    }
    
    const activeSessions = sessions.filter(s => 
        s.status === 'active' || s.state === 'running' || s.active === true
    );
    
    console.log('Active sessions found:', activeSessions.length);
    
    // Resto del código...
}
```

---

## 🟡 PROBLEMA #3: Total Events estático (siempre 36)

### Síntoma
El número 36 nunca cambia aunque se agreguen eventos.

### Causa
El cache no se está invalidando o los datos no se recargan.

### Archivo a corregir
`app/core/data_manager.py`

### Verificar
```python
def get_overview(self) -> Dict:
    """Get overview data (cached)"""
    def load():
        # FORZAR recarga de eventos para obtener conteo real
        self._load_events()  # <-- AGREGAR ESTA LÍNEA
        
        health = self._calculate_health()
        return {
            "health_score": health,
            "total_events": len(self._events),  # Debería ser dinámico
            ...
        }
    return self.get_cached("overview", load, ttl=10)
```

### O reducir el TTL del cache
```python
# Cambiar de 10 segundos a 5 para más actualizaciones
return self.get_cached("overview", load, ttl=5)
```

---

## 🟡 PROBLEMA #4: Health Score sin explicación

### Síntoma
```
44%
Overall system health based on recent events and performance
```

El usuario no sabe POR QUÉ es 44% ni qué lo afecta.

### Archivo a corregir
`app/core/data_manager.py` - Función `_calculate_health()`

### Código corregido
```python
def _calculate_health(self) -> dict:
    """
    Calculate health score with explanation.
    Returns dict with score and breakdown.
    """
    score = 100
    breakdown = []
    
    recent = self._events[:100]
    
    # Penalidades por severidad
    severity_penalties = {"S1": 15, "S2": 8, "S3": 3, "S4": 1}
    severity_counts = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
    
    for event in recent:
        severity = event.get('severity', 'S4')
        if severity in severity_penalties:
            score -= severity_penalties[severity]
            severity_counts[severity] += 1
    
    # Agregar al breakdown
    for sev, count in severity_counts.items():
        if count > 0:
            penalty = count * severity_penalties[sev]
            breakdown.append({
                "factor": f"{count} eventos {sev}",
                "impact": f"-{penalty}%",
                "description": f"Severidad {sev}: {count} eventos detectados"
            })
    
    # Penalizar por sesiones inactivas
    active_sessions = len([s for s in self._sessions.get('sessions', []) if s.get('status') == 'active'])
    if active_sessions == 0:
        score -= 20
        breakdown.append({
            "factor": "Sin sesiones activas",
            "impact": "-20%",
            "description": "No hay agentes monitoreados activamente"
        })
    
    final_score = max(0, min(100, score))
    
    return {
        "score": final_score,
        "breakdown": breakdown,
        "status": "healthy" if final_score >= 80 else "warning" if final_score >= 50 else "critical"
    }
```

### En el frontend
`ui/overview.html` - Agregar tooltip o detalle del health score

```javascript
function updateOverviewUI(data) {
    const health = data.health_score;
    
    // Si health es un objeto con breakdown
    if (typeof health === 'object') {
        elements.healthScore.textContent = `${health.score}%`;
        
        // Mostrar breakdown en tooltip o lista
        if (health.breakdown && health.breakdown.length > 0) {
            const breakdownHtml = health.breakdown.map(item => 
                `<div class="health-factor">
                    <span>${item.factor}</span>
                    <span class="impact">${item.impact}</span>
                </div>`
            ).join('');
            
            elements.healthBreakdown.innerHTML = breakdownHtml;
        }
    } else {
        // Backward compatibility - solo número
        elements.healthScore.textContent = `${health}%`;
    }
}
```

### Agregar en HTML
```html
<div class="metric-card">
    <div class="metric-header">
        <div class="metric-title">Health Score</div>
        <div class="metric-icon">❤️</div>
    </div>
    <div class="health-score health-score-ok" id="health-score">--</div>
    <div class="health-breakdown" id="health-breakdown">
        <!-- Aquí se mostrará el desglose -->
    </div>
    <div class="metric-description">
        Overall system health based on recent events and performance
    </div>
</div>
```

---

## 🟡 PROBLEMA #5: Skills sin descripción

### Síntoma
```
workspace-janitor
--
```

Solo muestra el nombre, la descripción es "--" o vacía.

### Archivo a corregir
`app/core/data_manager.py` - Función `_parse_skill()`

### Código actual
```python
def _parse_skill(self, skill_dir: Path) -> Optional[Dict]:
    skill_md = skill_dir / "SKILL.md"
    
    data = {
        "name": skill_dir.name,
        "description": "No description available"  # Default
    }
    
    if skill_md.exists():
        content = skill_md.read_text()[:500]
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                data["description"] = line.strip()[:100]
                break
```

### Código corregido
```python
def _parse_skill(self, skill_dir: Path) -> Optional[Dict]:
    """Parse skill with better description extraction."""
    
    data = {
        "name": skill_dir.name,
        "path": str(skill_dir),
        "description": "",
        "has_certification": (skill_dir / "CERTIFICATION.md").exists(),
        "has_scripts": False,
        "scripts_count": 0
    }
    
    # Contar scripts
    scripts = list(skill_dir.glob("scripts/*.py"))
    data["has_scripts"] = len(scripts) > 0
    data["scripts_count"] = len(scripts)
    
    # Buscar descripción en múltiples lugares
    description_sources = [
        skill_dir / "SKILL.md",
        skill_dir / "README.md",
        skill_dir / "description.txt",
        skill_dir / "manifest.json"
    ]
    
    for source in description_sources:
        if source.exists():
            try:
                if source.suffix == '.json':
                    with open(source, 'r') as f:
                        manifest = json.load(f)
                        data["description"] = manifest.get("description", "")
                else:
                    content = source.read_text(encoding='utf-8')
                    
                    # Buscar descripción en el contenido
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Saltar líneas vacías, títulos y metadata
                        if (line and 
                            not line.startswith('#') and 
                            not line.startswith('---') and
                            not line.startswith('```') and
                            len(line) > 10):
                            data["description"] = line[:150]
                            break
                
                if data["description"]:
                    break  # Encontramos descripción, salir del loop
                    
            except Exception as e:
                print(f"Error reading {source}: {e}")
    
    # Fallback: usar el nombre como descripción
    if not data["description"]:
        data["description"] = f"Skill: {skill_dir.name.replace('-', ' ').title()}"
    
    return data
```

---

## 🔴 PROBLEMA #6: Tabs de navegación no funcionan

### Síntoma
Los tabs (Operations, Skills, Logs, Search) no hacen nada al hacer click.

### Causa
Son solo anchors `<a href="#section">` sin lógica de routing ni contenido.

### Archivo a corregir
`ui/overview.html`

### Solución 1: Single Page con secciones (RECOMENDADO)

```html
<!-- Navigation -->
<nav class="nav-tabs">
    <a href="#overview" class="nav-tab active" data-section="overview">Overview</a>
    <a href="#operations" class="nav-tab" data-section="operations">Operations</a>
    <a href="#skills" class="nav-tab" data-section="skills">Skills</a>
    <a href="#logs" class="nav-tab" data-section="logs">Logs</a>
    <a href="#search" class="nav-tab" data-section="search">Search</a>
</nav>

<!-- Sections -->
<section id="section-overview" class="content-section active">
    <!-- Contenido actual del overview -->
</section>

<section id="section-operations" class="content-section" style="display: none;">
    <h2>Operations</h2>
    <p>Pendiente de implementar</p>
    <!-- TODO: Lista de operaciones en curso -->
</section>

<section id="section-skills" class="content-section" style="display: none;">
    <h2>Skills Registry</h2>
    <!-- TODO: Grid completo de skills con detalles -->
</section>

<section id="section-logs" class="content-section" style="display: none;">
    <h2>System Logs</h2>
    <!-- TODO: Visor de logs con filtros -->
</section>

<section id="section-search" class="content-section" style="display: none;">
    <h2>Search</h2>
    <input type="search" id="global-search" placeholder="Search events, skills, logs...">
    <div id="search-results"></div>
</section>
```

### JavaScript para navegación
```javascript
// Tab navigation
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
        e.preventDefault();
        
        const sectionId = tab.dataset.section;
        
        // Actualizar tabs activos
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Mostrar sección correspondiente
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });
        
        const targetSection = document.getElementById(`section-${sectionId}`);
        if (targetSection) {
            targetSection.style.display = 'block';
            
            // Cargar datos de la sección si es necesario
            loadSectionData(sectionId);
        }
    });
});

async function loadSectionData(sectionId) {
    switch(sectionId) {
        case 'overview':
            await refreshAllData();
            break;
        case 'operations':
            // TODO: Cargar operaciones
            break;
        case 'skills':
            await loadFullSkillsList();
            break;
        case 'logs':
            await loadLogs();
            break;
        case 'search':
            // El search se activa con el input
            break;
    }
}

async function loadFullSkillsList() {
    const data = await fetchData('/skills');
    // Renderizar lista completa de skills
}

async function loadLogs() {
    // TODO: Implementar endpoint /api/logs
    const data = await fetchData('/events?limit=100');
    // Renderizar como logs
}
```

### Solución 2: Páginas separadas (ALTERNATIVA)

Crear archivos separados:
- `ui/operations.html`
- `ui/skills.html`
- `ui/logs.html`
- `ui/search.html`

Y cambiar los links:
```html
<nav class="nav-tabs">
    <a href="/ui/overview.html" class="nav-tab active">Overview</a>
    <a href="/ui/operations.html" class="nav-tab">Operations</a>
    <a href="/ui/skills.html" class="nav-tab">Skills</a>
    <a href="/ui/logs.html" class="nav-tab">Logs</a>
    <a href="/ui/search.html" class="nav-tab">Search</a>
</nav>
```

---

## 🔴 PROBLEMA #7: No hay datos reales

### Síntoma general
Todo parece estático o placeholder.

### Diagnóstico requerido
Ejecutar estos comandos para verificar qué datos existen:

```bash
# Ver estructura de directorios de datos
ls -la ~/.openclaw/workspace/

# Ver eventos
ls -la ~/.openclaw/workspace/.system_events/
cat ~/.openclaw/workspace/.system_events/*.jsonl | head -5

# Ver watchdog
ls -la ~/.openclaw/workspace/.watchdog/
cat ~/.openclaw/workspace/.watchdog/session_registry.json

# Ver skills
ls -la ~/.openclaw/workspace/skills/
ls ~/.openclaw/workspace/skills/*/SKILL.md
```

### Si los directorios no existen
Crear datos de prueba:

```bash
# Crear directorios
mkdir -p ~/.openclaw/workspace/.system_events
mkdir -p ~/.openclaw/workspace/.watchdog
mkdir -p ~/.openclaw/workspace/skills/example-skill

# Crear evento de ejemplo
echo '{"type":"system_startup","severity":"S4","timestamp":"2024-01-01T00:00:00Z","source":"system","message":"System started"}' >> ~/.openclaw/workspace/.system_events/events.jsonl

# Crear sesión de ejemplo
echo '{"sessions":[{"id":"sess-001","status":"active","agent_id":"agent-main","label":"Main Agent","started_at":"2024-01-01T00:00:00Z"}]}' > ~/.openclaw/workspace/.watchdog/session_registry.json

# Crear skill de ejemplo
cat > ~/.openclaw/workspace/skills/example-skill/SKILL.md << 'EOF'
# Example Skill

This is an example skill for testing purposes.

## Features
- Feature 1
- Feature 2
EOF
```

---

## ✅ CHECKLIST DE CORRECCIONES

- [ ] Problema #1: Corregir mapeo de campos de eventos
- [ ] Problema #2: Corregir carga de sesiones
- [ ] Problema #3: Verificar actualización de contadores
- [ ] Problema #4: Agregar desglose del health score
- [ ] Problema #5: Mejorar extracción de descripción de skills
- [ ] Problema #6: Implementar navegación por tabs
- [ ] Problema #7: Verificar que existen datos reales
- [ ] Agregar console.log/print para debugging
- [ ] Probar cada endpoint con curl

### Comandos de prueba
```bash
# Health
curl http://localhost:8000/api/health

# Overview (ver estructura de datos)
curl http://localhost:8000/api/overview | python3 -m json.tool

# Events (ver campos disponibles)
curl http://localhost:8000/api/events?limit=1 | python3 -m json.tool

# Watchdog
curl http://localhost:8000/api/watchdog | python3 -m json.tool

# Skills
curl http://localhost:8000/api/skills | python3 -m json.tool
```

---

## 📌 ORDEN DE PRIORIDAD PARA CORREGIR

1. **PRIMERO:** Ejecutar diagnóstico (ver qué datos existen realmente)
2. **SEGUNDO:** Agregar debugging (console.log/print) para ver estructura de datos
3. **TERCERO:** Corregir mapeo de campos en frontend
4. **CUARTO:** Implementar navegación de tabs
5. **QUINTO:** Mejorar health score con desglose

---

**NO CONTINÚES HASTA VERIFICAR QUE LOS DATOS EXISTEN EN EL FILESYSTEM**

El 90% de estos problemas se resuelven cuando:
1. Los datos existen en los directorios correctos
2. El frontend mapea los campos correctos de los JSON
3. El backend lee los archivos correctos

**Fecha:** 2025-03-11  
**Autor:** Auditoría de código
