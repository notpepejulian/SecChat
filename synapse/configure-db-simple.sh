#!/bin/bash
# Script simplificado para configurar Synapse con MariaDB

echo "Configurando Synapse para MariaDB..."

# Cargar variables de entorno
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env no encontrado"
    exit 1
fi

# Configuración de base de datos para homeserver.yaml
DB_CONFIG="
database:
  name: pymysql
  args:
    host: db
    port: 3306
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    database: ${DB_NAME}
    cp_min: 5
    cp_max: 10
"

# Ejecutar dentro del contenedor de Synapse (si está corriendo)
docker-compose exec -T synapse sh -c "
cd /data
if [ ! -f homeserver.yaml.backup ]; then
    cp homeserver.yaml homeserver.yaml.backup
    echo 'Backup creado'
fi

# Comentar configuración SQLite existente
sed -i '/^database:/,/^[^ ]/ { /^database:/!{ /^[^ ]/!s/^/#/ } }' homeserver.yaml

# Agregar configuración MariaDB
cat >> homeserver.yaml << 'EOF'

# MariaDB Configuration
database:
  name: pymysql
  args:
    host: db
    port: 3306
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    database: ${DB_NAME}
    cp_min: 5
    cp_max: 10
EOF

echo 'Configuración actualizada'
" || {
    # Si Synapse no está corriendo, configurar directamente en el volumen
    docker run --rm -v chatsender_synapse_data:/data -e DB_USER="${DB_USER}" -e DB_PASSWORD="${DB_PASSWORD}" -e DB_NAME="${DB_NAME}" alpine sh -c "
        cd /data
        if [ ! -f homeserver.yaml.backup ]; then
            cp homeserver.yaml homeserver.yaml.backup
        fi
        
        # Comentar SQLite
        sed -i '/^database:/,/^[^ ]/ { /^database:/!{ /^[^ ]/!s/^/#/ } }' homeserver.yaml
        
        # Agregar MariaDB
        cat >> homeserver.yaml << EOF

# MariaDB Configuration  
database:
  name: pymysql
  args:
    host: db
    port: 3306
    user: \${DB_USER}
    password: \${DB_PASSWORD}
    database: \${DB_NAME}
    cp_min: 5
    cp_max: 10
EOF
        echo 'Configuración actualizada en volumen'
    "
}

echo "Synapse configurado para usar MariaDB"
echo "Reiniciando Synapse..."
docker-compose restart synapse
