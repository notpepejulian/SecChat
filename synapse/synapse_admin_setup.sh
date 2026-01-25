#!/bin/bash
#
# Script para configurar admin en Synapse y obtener token de acceso
#

echo "========================================="
echo "Configuración de Admin API en Synapse"
echo "========================================="
echo ""

# Verificar que los contenedores estén corriendo
if ! docker ps | grep -q chatsender_synapse; then
    echo "Error: El contenedor de Synapse no está corriendo"
    echo "   Inicia los servicios con: docker-compose up -d"
    exit 1
fi

echo "Paso 1: Crear usuario administrador"
echo "---------------------------------------"
echo ""

# Solicitar nombre de usuario admin
read -p "Nombre de usuario admin (ejemplo: admin): " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}

# Generar password aleatorio
ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

echo ""
echo "Creando usuario administrador..."
echo ""

# Crear usuario admin usando register_new_matrix_user
docker exec -it chatsender_synapse \
    register_new_matrix_user \
    -u ${ADMIN_USER} \
    -p ${ADMIN_PASSWORD} \
    -a \
    -c /data/homeserver.yaml \
    http://localhost:8008

if [ $? -ne 0 ]; then
    echo ""
    echo "Error al crear usuario administrador"
    echo "   El usuario puede ya existir, intenta con otro nombre"
    exit 1
fi

echo ""
echo "Usuario administrador creado:"
echo "   Usuario: @${ADMIN_USER}:${SYNAPSE_SERVER_NAME:-fed.local}"
echo "   Password: ${ADMIN_PASSWORD}"
echo ""
echo "IMPORTANTE: Guarda estas credenciales de forma segura"
echo ""

echo "Paso 2: Obtener token de acceso"
echo "---------------------------------------"
echo ""

# Obtener token usando la API de login
SYNAPSE_SERVER_NAME=${SYNAPSE_SERVER_NAME:-fed.local}
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost/_matrix/client/v3/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"type\": \"m.login.password\",
        \"identifier\": {
            \"type\": \"m.id.user\",
            \"user\": \"${ADMIN_USER}\"
        },
        \"password\": \"${ADMIN_PASSWORD}\"
    }")

# Extraer access_token del JSON response
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$ACCESS_TOKEN" ]; then
    echo " Error al obtener token de acceso"
    echo "   Respuesta del servidor: $TOKEN_RESPONSE"
    echo ""
    echo "   Puedes intentar obtenerlo manualmente:"
    echo "   1. Accede a http://localhost/_matrix/client/"
    echo "   2. Login con usuario: @${ADMIN_USER}:${SYNAPSE_SERVER_NAME} y password: ${ADMIN_PASSWORD}"
    echo "   3. El token estará en la respuesta JSON bajo 'access_token'"
    exit 1
fi

echo " Token de acceso obtenido"
echo ""

echo "========================================="
echo " Configuración completada"
echo "========================================="
echo ""
echo "Agrega el siguiente token a tu archivo .env:"
echo ""
echo "SYNAPSE_ADMIN_TOKEN=${ACCESS_TOKEN}"
echo ""
echo "Para copiar al archivo .env automáticamente:"
echo "  echo 'SYNAPSE_ADMIN_TOKEN=${ACCESS_TOKEN}' >> .env"
echo ""
echo "Credenciales del admin (guárdalas de forma segura):"
echo "  Usuario: @${ADMIN_USER}:${SYNAPSE_SERVER_NAME}"
echo "  Password: ${ADMIN_PASSWORD}"
echo "  Token: ${ACCESS_TOKEN}"
echo ""
