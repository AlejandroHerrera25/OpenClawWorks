#!/bin/bash
# Start OpenClaw Operations Center v2 - Simple version
# Uses system Python with minimal dependencies
#
# ✅ CORREGIDO: Puerto configurable y cleanup robusto

set -e

# ============================================
# CONFIGURACIÓN (via variables de entorno)
# ============================================
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "🚀 OPENCLAW OPERATIONS CENTER v2 - SIMPLE START"
echo "================================================"
echo "📌 Puerto configurado: $PORT"

# ============================================
# PASO 1: CLEANUP ROBUSTO
# ============================================
echo ""
echo "1. 🧹 Limpiando procesos anteriores..."

# Método 1: Matar por puerto (MÁS CONFIABLE)
if command -v fuser > /dev/null; then
    fuser -k ${PORT}/tcp 2>/dev/null || true
fi

# Método 2: Matar por nombre de proceso (backup)
pkill -f "uvicorn.*operations" 2>/dev/null || true
pkill -f "python3.*simple_server" 2>/dev/null || true
pkill -f "python.*server\.py" 2>/dev/null || true

# Esperar a que los procesos mueran
sleep 2

# ============================================
# PASO 2: VERIFICAR QUE EL PUERTO ESTÁ LIBRE
# ============================================
echo "2. 🔍 Verificando puerto $PORT..."

if lsof -i :${PORT} > /dev/null 2>&1; then
    echo "   ⚠️  Puerto $PORT aún ocupado, intentando liberar..."
    
    # Obtener PID y matar con -9
    PID=$(lsof -t -i :${PORT} 2>/dev/null || true)
    if [ -n "$PID" ]; then
        echo "   Matando proceso $PID..."
        kill -9 $PID 2>/dev/null || true
        sleep 2
    fi
    
    # Verificar de nuevo
    if lsof -i :${PORT} > /dev/null 2>&1; then
        echo "   ❌ No se pudo liberar el puerto $PORT"
        echo "   Procesos usando el puerto:"
        lsof -i :${PORT}
        
        # ALTERNATIVA: Buscar puerto disponible
        echo ""
        echo "   🔄 Buscando puerto alternativo..."
        for ALT_PORT in $(seq $((PORT+1)) $((PORT+10))); do
            if ! lsof -i :${ALT_PORT} > /dev/null 2>&1; then
                echo "   ✅ Usando puerto alternativo: $ALT_PORT"
                PORT=$ALT_PORT
                break
            fi
        done
    fi
fi

echo "   ✅ Puerto $PORT disponible"

# ============================================
# PASO 3: VERIFICAR PYTHON
# ============================================
echo ""
echo "3. 🐍 Verificando Python..."
cd "$(dirname "$0")"

if ! python3 -c "import http.server, json, sqlite3, threading" 2>/dev/null; then
    echo "   ❌ Módulos Python básicos no disponibles"
    exit 1
fi
echo "   ✅ Python OK"

# ============================================
# PASO 4: INICIAR SERVIDOR
# ============================================
echo ""
echo "4. 🚀 Iniciando servidor en puerto $PORT..."

mkdir -p logs

# Exportar puerto para que el script Python lo use
export PORT=$PORT

# Iniciar servidor con el puerto como argumento
nohup python3 app/api/simple_server.py $PORT > logs/server.log 2>&1 &
SERVER_PID=$!
echo "   PID del servidor: $SERVER_PID"

# Guardar PID para cleanup posterior
echo $SERVER_PID > logs/server.pid

# ============================================
# PASO 5: VERIFICAR QUE INICIÓ
# ============================================
echo ""
echo "5. ⏳ Esperando que el servidor inicie..."

max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:${PORT}/api/health > /dev/null 2>&1; then
        echo "   ✅ Servidor iniciado correctamente"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "   ❌ El servidor no respondió después de $max_attempts intentos"
        echo ""
        echo "   📋 Últimas líneas del log:"
        tail -20 logs/server.log
        exit 1
    fi
    
    echo "   Intento $attempt/$max_attempts..."
    sleep 1
    attempt=$((attempt + 1))
done

# ============================================
# INFORMACIÓN FINAL
# ============================================
echo ""
echo "================================================"
echo "✅ OPENCLAW OPERATIONS CENTER v2 LISTO"
echo "================================================"
echo ""
echo "🔗 URLs DE ACCESO:"
echo "   • UI Overview:      http://localhost:${PORT}/ui/overview.html"
echo "   • REST API:         http://localhost:${PORT}/api/*"
echo "   • Health check:     http://localhost:${PORT}/api/health"
echo ""
echo "🛑 PARA DETENER:"
echo "   kill $SERVER_PID"
echo "   # o"
echo "   kill \$(cat logs/server.pid)"
echo "   # o"
echo "   fuser -k ${PORT}/tcp"
echo ""
echo "📋 VER LOGS:"
echo "   tail -f logs/server.log"
echo ""

# Abrir navegador si es posible
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:${PORT}/ui/overview.html" 2>/dev/null &
elif command -v open > /dev/null; then
    open "http://localhost:${PORT}/ui/overview.html" 2>/dev/null &
else
    echo "💡 Abre manualmente: http://localhost:${PORT}/ui/overview.html"
fi

echo "✅ Sistema corriendo. Ctrl+C para ver logs en vivo."
echo ""

# Mostrar logs
tail -f logs/server.log
