#!/usr/bin/env python3
"""
DataManager Singleton para OpenClaw Operations Center v2
Implementa la arquitectura recomendada por emergent.sh:
- Singleton que gestiona todo el estado en memoria
- FileWatcher para invalidación automática cuando archivos cambian
- SQLite FTS5 para búsqueda rápida (O(log n) vs O(n*m))
- Cache con TTL y refresh automático
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import threading
from dataclasses import dataclass, field
import time

# Try to import watchdog, but provide fallback if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️  Watchdog not available, file watching disabled")

@dataclass
class CacheEntry:
    """Entry in the cache with TTL"""
    data: Any
    timestamp: datetime
    ttl_seconds: int = 30
    
    @property
    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        return (datetime.now() - self.timestamp).total_seconds() < self.ttl_seconds

class DataManager:
    """Singleton que gestiona todo el estado en memoria con invalidación inteligente"""
    
    _instance: Optional['DataManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Paths to data directories
        self.workspace_path = Path.home() / ".openclaw" / "workspace"
        self.events_dir = self.workspace_path / ".system_events"
        self.watchdog_dir = self.workspace_path / ".watchdog"
        self.skills_dir = self.workspace_path / "skills"
        self.learnings_dir = self.workspace_path / ".learnings"
        
        # In-memory state
        self._events: List[Dict] = []
        self._sessions: Dict[str, Any] = {}
        self._skills: Dict[str, Any] = {}
        self._metrics: Dict[str, Any] = {}
        self._incidents: List[Dict] = []
        
        # Cache with TTL
        self._cache: Dict[str, CacheEntry] = {}
        
        # WebSocket subscribers for real-time updates
        self._subscribers: List[Callable] = []
        
        # SQLite for FTS5 search
        self._init_search_db()
        
        # FileWatcher for automatic cache invalidation
        self._init_file_watcher()
        
        # Initial data load
        self._load_all_data()
        
        self._initialized = True
        print(f"✅ DataManager initialized with {len(self._events)} events, {len(self._skills)} skills")
    
    def _init_search_db(self):
        """Initialize SQLite with FTS5 for fast search"""
        self._db_path = Path("/tmp/operations_search_v2.db")
        self._db = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._db_lock = threading.Lock()
        
        with self._db_lock:
            # Create FTS5 virtual table for full-text search
            self._db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    id,
                    type,
                    content,
                    metadata,
                    timestamp,
                    tokenize='porter unicode61'
                )
            """)
            
            # Create metadata table
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS search_meta (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    source_file TEXT,
                    raw_data TEXT
                )
            """)
            
            self._db.commit()
    
    def _init_file_watcher(self):
        """Initialize FileWatcher for automatic cache invalidation"""
        if not WATCHDOG_AVAILABLE:
            print("⚠️  File watching disabled (watchdog not installed)")
            return
        
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, manager: 'DataManager'):
                self.manager = manager
                self._debounce_timers: Dict[str, threading.Timer] = {}
            
            def _debounced_reload(self, path: str):
                """Debounce to avoid multiple reloads in quick succession"""
                if path in self._debounce_timers:
                    self._debounce_timers[path].cancel()
                
                timer = threading.Timer(0.5, lambda: self.manager._on_file_change(path))
                self._debounce_timers[path] = timer
                timer.start()
            
            def on_modified(self, event):
                if not event.is_directory:
                    self._debounced_reload(event.src_path)
            
            def on_created(self, event):
                if not event.is_directory:
                    self._debounced_reload(event.src_path)
        
        self._observer = Observer()
        handler = ChangeHandler(self)
        
        # Watch directories if they exist
        for dir_path in [self.events_dir, self.watchdog_dir, self.skills_dir, self.learnings_dir]:
            if dir_path.exists():
                self._observer.schedule(handler, str(dir_path), recursive=True)
        
        self._observer.start()
        print("✅ FileWatcher started")
    
    def _on_file_change(self, path: str):
        """Callback when a file changes - invalidate relevant cache and reload"""
        path_obj = Path(path)
        
        if ".system_events" in str(path_obj):
            self._invalidate_cache("events")
            self._load_events()
        elif ".watchdog" in str(path_obj):
            self._invalidate_cache("watchdog")
            self._load_watchdog()
        elif "skills" in str(path_obj):
            self._invalidate_cache("skills")
            self._load_skills()
        elif ".learnings" in str(path_obj):
            self._invalidate_cache("incidents")
            self._load_incidents()
        
        print(f"📁 File changed: {path}, cache invalidated")
        
        # Notify WebSocket subscribers
        self._broadcast_update_async(path)
    
    def _invalidate_cache(self, prefix: str):
        """Invalidate all cache entries starting with prefix"""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]
    
    def _load_all_data(self):
        """Load all initial data"""
        self._load_events()
        self._load_watchdog()
        self._load_skills()
        self._load_incidents()
        self._rebuild_search_index()
    
    def _load_events(self):
        """Load events from .system_events/"""
        events = []
        if self.events_dir.exists():
            for event_file in self.events_dir.glob("*.jsonl"):
                try:
                    with open(event_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                events.append(json.loads(line))
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading {event_file}: {e}")
        
        # Sort by timestamp descending
        events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        self._events = events
    
    def _load_watchdog(self):
        """Load watchdog data"""
        self._sessions = {}
        self._metrics = {}
        
        session_file = self.watchdog_dir / "session_registry.json"
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    self._sessions = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        metrics_file = self.watchdog_dir / "metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    self._metrics = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
    
    def _load_skills(self):
        """Load skills registry"""
        skills = {}
        if self.skills_dir.exists():
            for skill_dir in self.skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_data = self._parse_skill(skill_dir)
                    if skill_data:
                        skills[skill_dir.name] = skill_data
        
        self._skills = skills
    
    def _parse_skill(self, skill_dir: Path) -> Optional[Dict]:
        """Parse an individual skill"""
        skill_md = skill_dir / "SKILL.md"
        
        data = {
            "name": skill_dir.name,
            "path": str(skill_dir),
            "has_certification": (skill_dir / "CERTIFICATION.md").exists(),
            "has_scripts": len(list(skill_dir.glob("scripts/*.py"))) > 0,
            "scripts_count": len(list(skill_dir.glob("scripts/*.py")))
        }
        
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding='utf-8')[:500]  # First 500 chars
                # Extract first line as description
                lines = content.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        data["description"] = line.strip()[:100]
                        break
                if "description" not in data:
                    data["description"] = "No description available"
            except IOError:
                data["description"] = "Error reading description"
        
        return data
    
    def _load_incidents(self):
        """Load incidents from .learnings/"""
        incidents = []
        if self.learnings_dir.exists():
            incidents_file = self.learnings_dir / "LEARNINGS.md"
            if incidents_file.exists():
                try:
                    content = incidents_file.read_text(encoding='utf-8')
                    # Simple parsing of incidents
                    lines = content.split('\n')
                    current_incident = {}
                    for line in lines:
                        if line.startswith('### '):
                            if current_incident:
                                incidents.append(current_incident)
                            current_incident = {"title": line[4:].strip()}
                        elif line.startswith('- **Pattern‑Key**:'):
                            current_incident["pattern_key"] = line.split(': ')[1].strip()
                        elif line.startswith('- **Date**:'):
                            current_incident["date"] = line.split(': ')[1].strip()
                    
                    if current_incident:
                        incidents.append(current_incident)
                except IOError as e:
                    print(f"Error loading incidents: {e}")
        
        self._incidents = incidents
    
    def _rebuild_search_index(self):
        """Rebuild FTS5 search index"""
        with self._db_lock:
            # Clear previous index
            self._db.execute("DELETE FROM search_index")
            self._db.execute("DELETE FROM search_meta")
            
            # Index events
            for i, event in enumerate(self._events[:1000]):  # Limit to 1000 events
                event_id = f"event_{i}"
                content = json.dumps(event, default=str)
                self._db.execute(
                    "INSERT INTO search_index (id, type, content, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (event_id, "event", content, event.get('type', ''), event.get('timestamp', ''))
                )
                self._db.execute(
                    "INSERT INTO search_meta (id, type, source_file, raw_data) VALUES (?, ?, ?, ?)",
                    (event_id, "event", "", content)
                )
            
            # Index skills
            for skill_name, skill_data in self._skills.items():
                skill_id = f"skill_{skill_name}"
                content = json.dumps(skill_data, default=str)
                self._db.execute(
                    "INSERT INTO search_index (id, type, content, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (skill_id, "skill", content, skill_name, "")
                )
            
            self._db.commit()
    
    # ========== PUBLIC API ==========
    
    def get_cached(self, key: str, loader: Callable, ttl: int = 30) -> Any:
        """Get data from cache or load it if not exists/expired"""
        if key in self._cache and self._cache[key].is_valid:
            return self._cache[key].data
        
        data = loader()
        self._cache[key] = CacheEntry(data=data, timestamp=datetime.now(), ttl_seconds=ttl)
        return data
    
    def get_overview(self) -> Dict:
        """Get overview data (cached)"""
        def load():
            health = self._calculate_health()
            return {
                "health_score": health,
                "total_events": len(self._events),
                "recent_events": self._events[:10],
                "active_sessions": len([s for s in self._sessions.get('sessions', []) if s.get('status') == 'active']),
                "total_skills": len(self._skills),
                "certified_skills": len([s for s in self._skills.values() if s.get('has_certification')]),
                "scripts_count": sum([s.get('scripts_count', 0) for s in self._skills.values()]),
                "last_update": datetime.now().isoformat(),
                "system_uptime": self._get_system_uptime()
            }
        return self.get_cached("overview", load, ttl=10)
    
    def get_events(self, limit: int = 50, offset: int = 0) -> Dict:
        """Get paginated events"""
        return {
            "events": self._events[offset:offset + limit],
            "total": len(self._events),
            "limit": limit,
            "offset": offset
        }
    
    def get_watchdog_status(self) -> Dict:
        """Get watchdog status"""
        def load():
            return {
                "sessions": self._sessions,
                "metrics": self._metrics,
                "health": "healthy" if self._metrics else "unknown",
                "active_count": len([s for s in self._sessions.get('sessions', []) if s.get('status') == 'active'])
            }
        return self.get_cached("watchdog", load, ttl=15)
    
    def get_skills(self) -> Dict:
        """Get skills registry"""
        return {
            "skills": list(self._skills.values()),
            "total": len(self._skills),
            "certified": len([s for s in self._skills.values() if s.get('has_certification')]),
            "with_scripts": len([s for s in self._skills.values() if s.get('has_scripts')])
        }
    
    def get_incidents(self) -> Dict:
        """Get incidents/learnings"""
        def load():
            return {
                "incidents": self._incidents,
                "total": len(self._incidents),
                "last_24h": len([i for i in self._incidents if self._is_recent(i.get('date', ''))])
            }
        return self.get_cached("incidents", load, ttl=60)
    
    def search(self, query: str, limit: int = 50) -> List[Dict]:
        """FTS5 search - O(log n) instead of O(n*m)"""
        if not query or len(query) < 2:
            return []
        
        results = []
        with self._db_lock:
            # FTS5 search with ranking
            cursor = self._db.execute("""
                SELECT search_meta.id, search_meta.type, search_meta.raw_data,
                       bm25(search_index) as rank
                FROM search_index
                JOIN search_meta ON search_index.id = search_meta.id
                WHERE search_index MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            
            for row in cursor:
                try:
                    results.append({
                        "id": row[0],
                        "type": row[1],
                        "data": json.loads(row[2]),
                        "score": abs(row[3])
                    })
                except json.JSONDecodeError:
                    pass
        
        return results
    
    def _calculate_health(self) -> int:
        """Calculate health score based on recent events"""
        score = 100
        recent = self._events[:100]  # Only last 100 events
        
        severity_penalties = {"S1": 15, "S2": 8, "S3": 3, "S4": 1}
        
        for event in recent:
            severity = event.get('severity', 'S4')
            score -= severity_penalties.get(severity, 0)
        
        # Penalize for inactive sessions
        active_sessions = len([s for s in self._sessions.get('sessions', []) if s.get('status') == 'active'])
        if active_sessions == 0:
            score -= 20
        
        return max(0, min(100, score))
    
    def _get_system_uptime(self) -> str:
        """Calculate system uptime based on events"""
        if not self._events:
            return "unknown"
        
        try:
            # Find the oldest event
            oldest_event = min(self._events, key=lambda x: x.get('timestamp', ''))
            oldest_time = datetime.fromisoformat(oldest_event.get('timestamp').replace('Z', '+00:00'))
            uptime_days = (datetime.now() - oldest_time).days
            
            if uptime_days == 0:
                return "<1 day"
            elif uptime_days == 1:
                return "1 day"
            else:
                return f"{uptime_days} days"
        except:
            return "unknown"
    
    def _is_recent(self, date_str: str) -> bool:
        """Check if date is within last 24 hours"""
        if not date_str:
            return False
        
        try:
            event_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return (datetime.now() - event_date).days < 1
        except:
            return False
    
    def _broadcast_update_async(self, changed_path: str):
        """Broadcast update to all subscribers (async)"""
        update = {
            "type": "data_update",
            "path": changed_path,
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, this would use asyncio
        # For now, just print
        print(f"📡 Broadcast update: {update}")
    
    def subscribe(self, callback: Callable):
        """Subscribe a callback for real-time updates"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe a callback"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def shutdown(self):
        """Cleanup on shutdown"""
        if WATCHDOG_AVAILABLE and hasattr(self, '_observer'):
            self._observer.stop()
            self._observer.join()
        
        if hasattr(self, '_db'):
            self._db.close()
        
        print("✅ DataManager shutdown complete")

# Global instance
data_manager = DataManager()