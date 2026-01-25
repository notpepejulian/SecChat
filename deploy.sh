#!/bin/bash
#
# Script de despliegue de ChatSender
# Uso: ./deploy.sh [dev|prod]
#

set -e

MODE="${1:-dev}"
COMPOSE_FILE="docker-compose.dev.yml"

if [ "$MODE" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "========================================="
echo "Desplegando ChatSender en modo: $MODE"
echo "Usando archivo: $COMPOSE_FILE"
echo "========================================="

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "❌ ERROR: No existe el archivo .env"
    echo "Copia .env.example a .env y configura tus credenciales:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Verificar que Synapse está inicializado
if [ ! -f "./synapse_data/homeserver.yaml" ]; then
    echo "⚠️  ADVERTENCIA: Synapse no parece estar inicializado"
    echo "Ejecuta ./synapse/init-synapse.sh primero"
    read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detener contenedores existentes
echo ""
echo "📦 Deteniendo contenedores existentes..."
docker-compose -f "$COMPOSE_FILE" down

# Construir imágenes
echo ""
echo "🔨 Construyendo imágenes..."
docker-compose -f "$COMPOSE_FILE" build --no-cache

# Iniciar servicios
echo ""
echo "🚀 Iniciando servicios..."
docker-compose -f "$COMPOSE_FILE" up -d

# Esperar a que los servicios estén listos
echo ""
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado
echo ""
echo "📊 Estado de los servicios:"
docker-compose -f "$COMPOSE_FILE" ps

# Healthcheck manual
echo ""
echo "🏥 Verificando salud de los servicios..."
echo ""

# Verificar DB
echo -n "MariaDB: "
if docker exec chatsender_db mariadb-admin ping -h localhost --silent &>/dev/null; then
    echo "✅ OK"
else
    echo "❌ FAIL"
fi

# Verificar Backend
echo -n "Backend: "
if curl -s http://localhost/api/health &>/dev/null; then
    echo "✅ OK"
else
    echo "❌ FAIL"
fi

# Verificar Synapse
echo -n "Synapse: "
if curl -s http://localhost/_matrix/client/versions &>/dev/null; then
    echo "✅ OK"
else
    echo "❌ FAIL"
fi

# Verificar Frontend
echo -n "Frontend: "
if curl -s http://localhost/ &>/dev/null; then
    echo "✅ OK"
else
    echo "❌ FAIL"
fi

echo ""
echo "========================================="
echo "✅ Despliegue completado"
echo "========================================="
echo ""
echo "Acceso:"
echo "  - Frontend: http://localhost"
echo "  - Backend API: http://localhost/api"
echo "  - Synapse: http://localhost/_matrix"
echo ""
echo "Comandos útiles:"
echo "  - Ver logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  - Ver estado: docker-compose -f $COMPOSE_FILE ps"
echo "  - Detener: docker-compose -f $COMPOSE_FILE down"
echo ""
