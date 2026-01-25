#!/bin/bash
#
# Script auxiliar para gestionar llaves desde fuera del contenedor
# Uso: ./keygen.sh [comando]
#

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED} Error: Docker no está corriendo.${NC}"
    echo "   Inicia Docker e intenta de nuevo."
    exit 1
fi

# Verificar si el contenedor existe
if ! docker ps -a --format '{{.Names}}' | grep -q '^chatsender_backend$'; then
    echo -e "${RED} Error: El contenedor 'chatsender_backend' no existe.${NC}"
    echo "   Ejecuta 'docker compose up -d' primero."
    exit 1
fi

# Verificar si el contenedor está corriendo
if ! docker ps --format '{{.Names}}' | grep -q '^chatsender_backend$'; then
    echo -e "${YELLOW}  El contenedor 'chatsender_backend' no está corriendo.${NC}"
    echo "   Iniciando contenedor..."
    docker compose up -d backend
    sleep 3
fi

# Ejecutar el comando en el contenedor
echo -e "${GREEN} Ejecutando en contenedor backend...${NC}\n"
docker exec -it chatsender_backend python cli_keygen.py "$@"
