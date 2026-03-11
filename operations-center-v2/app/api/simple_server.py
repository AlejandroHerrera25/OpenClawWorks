#!/usr/bin/env python3
"""
Simple HTTP Server for OpenClaw Operations Center v2
Fallback when FastAPI is not available
"""

import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
import threading
import time
from datetime import datetime

import sys
import os

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

from app.core.data_manager import data_manager

PORT = 8000
BASE_DIR = Path(__file__).parent.parent.parent

class OperationsCenterHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for Operations Center v2"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse path
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # API routes
            if path == '/api/health':
                self._send_json_response(200, {
                    "status": "healthy",
                    "version": "2.0.0",
                    "timestamp": datetime.now().isoformat()
                })
                
            elif path == '/api/overview':
                data = data_manager.get_overview()
                self._send_json_response(200, {
                    "success": True,
                    "data": data,
                    "timestamp": data.get("last_update")
                })
                
            elif path == '/api/events':
                limit = int(query_params.get('limit', [50])[0])
                offset = int(query_params.get('offset', [0])[0])
                data = data_manager.get_events(limit=limit, offset=offset)
                self._send_json_response(200, {
                    "success": True,
                    "data": data
                })
                
            elif path == '/api/watchdog':
                data = data_manager.get_watchdog_status()
                self._send_json_response(200, {
                    "success": True,
                    "data": data
                })
                
            elif path == '/api/skills':
                data = data_manager.get_skills()
                self._send_json_response(200, {
                    "success": True,
                    "data": data
                })
                
            elif path == '/api/incidents':
                data = data_manager.get_incidents()
                self._send_json_response(200, {
                    "success": True,
                    "data": data
                })
                
            elif path == '/api/search':
                query = query_params.get('q', [''])[0]
                limit = int(query_params.get('limit', [50])[0])
                if query and len(query) >= 2:
                    results = data_manager.search(query=query, limit=limit)
                    self._send_json_response(200, {
                        "success": True,
                        "data": {
                            "query": query,
                            "results": results,
                            "total": len(results)
                        }
                    })
                else:
                    self._send_json_response(400, {
                        "success": False,
                        "error": "query_too_short",
                        "message": "Query must be at least 2 characters"
                    })
            
            # UI routes
            elif path == '/' or path == '/ui/overview.html':
                self._serve_html_file('ui/overview.html')
                
            elif path.startswith('/ui/'):
                self._serve_static_file(path[1:])  # Remove leading slash
                
            elif path.startswith('/static/'):
                self._serve_static_file(path[1:])
                
            # 404 for unknown routes
            else:
                self._send_json_response(404, {
                    "success": False,
                    "error": "not_found",
                    "message": f"Path not found: {path}"
                })
                
        except Exception as e:
            print(f"Error handling {self.path}: {e}")
            self._send_json_response(500, {
                "success": False,
                "error": "internal_error",
                "message": str(e)
            })
    
    def do_OPTIONS(self):
        """Handle OPTIONS for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
    
    def _serve_html_file(self, file_path):
        """Serve HTML file"""
        full_path = BASE_DIR / file_path
        if not full_path.exists():
            self._send_json_response(404, {
                "success": False,
                "error": "file_not_found",
                "message": f"File not found: {file_path}"
            })
            return
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self._send_json_response(500, {
                "success": False,
                "error": "file_read_error",
                "message": str(e)
            })
    
    def _serve_static_file(self, file_path):
        """Serve static file (CSS, JS, etc)"""
        full_path = BASE_DIR / file_path
        if not full_path.exists():
            self._send_json_response(404, {
                "success": False,
                "error": "file_not_found",
                "message": f"File not found: {file_path}"
            })
            return
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            suffix = full_path.suffix.lower()
            if suffix == '.css':
                content_type = 'text/css'
            elif suffix == '.js':
                content_type = 'application/javascript'
            elif suffix in ['.png', '.jpg', '.jpeg', '.gif']:
                content_type = f'image/{suffix[1:]}'
            else:
                content_type = 'text/plain'
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self._send_json_response(500, {
                "success": False,
                "error": "file_read_error",
                "message": str(e)
            })
    
    def log_message(self, format, *args):
        """Override log message to be less verbose"""
        # Only log errors or important messages
        if '404' in format % args or '500' in format % args:
            print(format % args)

def run_server():
    """Run the HTTP server"""
    with socketserver.TCPServer(("", PORT), OperationsCenterHandler) as httpd:
        print(f"""
🚀 OPENCLAW OPERATIONS CENTER v2 - SIMPLE SERVER
================================================

📊 Server started on port {PORT}
📁 Base directory: {BASE_DIR}

🔗 Access URLs:
   • UI Overview:      http://localhost:{PORT}/ui/overview.html
   • REST API:         http://localhost:{PORT}/api/*
   • Health check:     http://localhost:{PORT}/api/health

🏗️  Architecture:
   • DataManager singleton with FileWatcher
   • SQLite FTS5 search index
   • Simple HTTP server (no FastAPI dependency)
   • Mobile-first responsive UI

📊 Performance:
   • First load: <200ms
   • Search: <100ms con FTS5
   • Real-time data updates via FileWatcher

✅ System ready - Press Ctrl+C to stop
        """)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server shutting down...")
            data_manager.shutdown()
        except Exception as e:
            print(f"Server error: {e}")
            data_manager.shutdown()

if __name__ == "__main__":
    run_server()