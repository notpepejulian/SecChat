#!/bin/bash
#
# Script de inicialización de Synapse
# Este script genera la configuración inicial de homeserver.yaml
#

echo "========================================="
echo "Inicializando configuración de Synapse"
echo "========================================="

# Verificar que el volumen synapse_data existe
if [ ! -d "./synapse_data" ]; then
    echo "Creando directorio temporal para generar configuración..."
    mkdir -p ./synapse_data
fi

echo ""
echo "Generando homeserver.yaml..."
echo ""

# Generar la configuración base de Synapse
docker run --rm \
    -v synapse_data:/data \
    -e SYNAPSE_SERVER_NAME=${SYNAPSE_SERVER_NAME:-fed.local} \
    -e SYNAPSE_REPORT_STATS=no \
    matrixdotorg/synapse:develop generate

echo ""
echo "========================================="
echo "Configuración generada exitosamente"
echo "========================================="
echo ""
echo "IMPORTANTE: Ahora debes configurar Synapse para usar MariaDB"
echo "Edita el archivo homeserver.yaml en el volumen synapse_data"
echo ""
echo "Para acceder al archivo, ejecuta:"
echo "  docker run --rm -it -v synapse_data:/data alpine sh"
echo "  cd /data && vi homeserver.yaml"
echo ""
echo "Busca la sección 'database:' y reemplázala con:"
echo ""
echo "database:"
echo "  name: psycopg2"
echo "  args:"
echo "    user: synapse_user"
echo "    password: <DB_PASSWORD>"
echo "    database: synapse"
echo "    host: db"
echo "    port: 3306"
echo "    cp_min: 5"
echo "    cp_max: 10"
echo ""
echo "NOTA: Synapse usa 'psycopg2' como nombre incluso para MySQL/MariaDB"
echo "      con el driver PyMySQL."
echo ""
