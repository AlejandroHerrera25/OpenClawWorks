#!/usr/bin/env python3
"""
FastAPI Gateway para OpenClaw Operations Center v2
Arquitectura recomendada por emergent.sh
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
import json
import os
from pathlib import Path

from ..core.data_manager import data_manager

# Connection manager para WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"👋 WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management - suscribe WebSocket broadcast a updates del DataManager"""
    print("🚀 Starting Operations Center v2...")
    
    # Suscribir el broadcast de WebSocket a updates del DataManager
    async def on_data_update(update: dict):
        await manager.broadcast(update)
    
    data_manager.subscribe(on_data_update)
    
    yield
    
    # Cleanup
    print("🛑 Shutting down Operations Center v2...")
    data_manager.unsubscribe(on_data_update)
    data_manager.shutdown()

app = FastAPI(
    title="OpenClaw Operations Center API v2",
    description="High-performance async API with WebSocket support",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ========== ERROR HANDLING ==========

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with fallback data"""
    print(f"⚠️  API Error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "internal_error",
            "message": str(exc),
            "fallback_data": get_fallback_data(request.url.path)
        }
    )

def get_fallback_data(path: str) -> dict:
    """Datos fallback cuando hay error - UI nunca se queda colgada"""
    fallbacks = {
        "/api/health": {"status": "error", "message": "Health check unavailable"},
        "/api/overview": {
            "health_score": -1,
            "status": "error",
            "message": "Overview data unavailable",
            "total_events": 0,
            "active_sessions": 0,
            "total_skills": 0
        },
        "/api/events": {"events": [], "total": 0, "status": "error"},
        "/api/watchdog": {"sessions": [], "active_sessions": 0, "status": "error"},
        "/api/skills": {"skills": [], "total": 0, "status": "error"},
        "/api/incidents": {"incidents": [], "total": 0, "status": "error"},
        "/api/search": {"results": [], "total": 0, "status": "error"},
    }
    
    for prefix, data in fallbacks.items():
        if path.startswith(prefix):
            return data
    
    return {"status": "error", "message": "Unknown endpoint"}

# ========== REST ENDPOINTS ==========

@app.get("/")
async def root():
    """Root endpoint - redirects to overview"""
    return {"message": "OpenClaw Operations Center v2", "docs": "/docs", "api_base": "/api"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": data_manager.get_overview().get("last_update"),
        "data_manager": "initialized"
    }

@app.get("/api/overview")
async def get_overview():
    """Dashboard overview - datos agregados"""
    return {
        "success": True,
        "data": data_manager.get_overview(),
        "timestamp": data_manager.get_overview().get("last_update")
    }

@app.get("/api/events")
async def get_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    severity: Optional[str] = Query(None, regex="^(S1|S2|S3|S4)$")
):
    """Eventos paginados con filtro opcional por severidad"""
    events_data = data_manager.get_events(limit=limit, offset=offset)
    
    if severity:
        filtered_events = [e for e in events_data["events"] if e.get("severity") == severity]
        events_data["events"] = filtered_events
        events_data["filtered_total"] = len(filtered_events)
    
    return {
        "success": True,
        "data": events_data,
        "filters": {"severity": severity} if severity else {}
    }

@app.get("/api/watchdog")
async def get_watchdog():
    """Estado del watchdog"""
    return {
        "success": True,
        "data": data_manager.get_watchdog_status()
    }

@app.get("/api/skills")
async def get_skills():
    """Registry de skills"""
    return {
        "success": True,
        "data": data_manager.get_skills()
    }

@app.get("/api/incidents")
async def get_incidents():
    """Incidentes de aprendizaje"""
    return {
        "success": True,
        "data": data_manager.get_incidents()
    }

@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(default=50, ge=1, le=100)
):
    """Búsqueda global con FTS5"""
    results = data_manager.search(query=q, limit=limit)
    return {
        "success": True,
        "data": {
            "query": q,
            "results": results,
            "total": len(results),
            "types": self._group_results_by_type(results)
        }
    }

def _group_results_by_type(self, results: List[Dict]) -> Dict:
    """Agrupa resultados por tipo"""
    types = {}
    for result in results:
        result_type = result.get("type", "unknown")
        if result_type not in types:
            types[result_type] = 0
        types[result_type] += 1
    return types

# ========== WEBSOCKET ENDPOINT ==========

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para updates real-time"""
    await manager.connect(websocket)
    
    try:
        # Enviar estado inicial
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "overview": data_manager.get_overview(),
                "timestamp": data_manager.get_overview().get("last_update")
            }
        })
        
        # Mantener conexión y recibir mensajes
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # Heartbeat cada 30s
                )
                
                # Manejar diferentes tipos de mensajes
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": data.get("timestamp")})
                elif data.get("type") == "subscribe":
                    # Suscribirse a canales específicos
                    channel = data.get("channel", "all")
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": channel,
                        "timestamp": data_manager.get_overview().get("last_update")
                    })
                elif data.get("type") == "refresh":
                    # Solicitar refresh manual
                    await websocket.send_json({
                        "type": "data_refresh",
                        "data": data_manager.get_overview(),
                        "timestamp": data_manager.get_overview().get("last_update")
                    })
                
            except asyncio.TimeoutError:
                # Enviar heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": data_manager.get_overview().get("last_update"),
                    "connections": len(manager.active_connections)
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"⚠️  WebSocket error: {e}")
        manager.disconnect(websocket)

# ========== STATIC FILE SERVING ==========

@app.get("/ui/{path:path}")
async def serve_ui(path: str):
    """Servir archivos de UI"""
    ui_dir = Path(__file__).parent.parent.parent / "ui"
    file_path = ui_dir / path
    
    if not file_path.exists():
        # Si no existe, intentar con extensiones comunes
        for ext in [".html", ".js", ".css"]:
            alt_path = ui_dir / f"{path}{ext}"
            if alt_path.exists():
                file_path = alt_path
                break
    
    if file_path.exists():
        if file_path.suffix == ".html":
            return HTMLResponse(content=file_path.read_text())
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="File not found")

# ========== MAIN ENTRY POINT ==========

if __name__ == "__main__":
    import uvicorn
    
    print("""
    🚀 OPENCLAW OPERATIONS CENTER v2
    ================================
    
    📊 API Endpoints:
      • REST API:      http://localhost:8000/api/*
      • WebSocket:     ws://localhost:8000/ws/live
      • Documentation: http://localhost:8000/docs
      • UI:           http://localhost:8000/ui/overview.html
    
    🔧 Architecture:
      • FastAPI async
      • DataManager singleton with FileWatcher
      • SQLite FTS5 search index
      • WebSocket real-time updates
    
    ✅ Expected performance:
      • First load: <200ms
      • Subsequent: <50ms
      • Search: <100ms
      • Concurrent users: 50+
    """)
    
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )