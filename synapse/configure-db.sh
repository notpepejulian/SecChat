#!/bin/bash
#
# Script para configurar Synapse con MariaDB
# Este script modifica el homeserver.yaml para usar MariaDB en lugar de SQLite
#

echo "========================================="
echo "Configurando Synapse para usar MariaDB"
echo "========================================="

# Cargar variables de entorno
if [ -f ".env" ]; then
    source .env
else
    echo "Error: archivo .env no encontrado"
    exit 1
fi

echo "Accediendo al volumen de Synapse..."

# Crear un script temporal que se ejecutará dentro del contenedor
cat > /tmp/synapse_db_config.sh << 'EOFSCRIPT'
#!/bin/sh
cd /data

# Backup del archivo original
if [ ! -f homeserver.yaml.backup ]; then
    cp homeserver.yaml homeserver.yaml.backup
    echo "Backup creado: homeserver.yaml.backup"
fi

# Verificar si ya está configurado para MariaDB
if grep -q "name: pymysql" homeserver.yaml; then
    echo "MariaDB ya está configurado"
    exit 0
fi

# Comentar la configuración SQLite existente y añadir MariaDB
sed -i '/^database:/,/^[^ ]/ {
    /^database:/!{
        /^[^ ]/!s/^/#/
    }
}' homeserver.yaml

# Añadir configuración de MariaDB al final del archivo
cat >> homeserver.yaml << EOF

# MariaDB Database Configuration
database:
  name: pymysql
  args:
    host: db
    port: 3306
    user: synapse_user
    password: ${DB_PASSWORD}
    database: synapse
    cp_min: 5
    cp_max: 10
EOF

echo "Configuración de MariaDB añadida"
EOFSCRIPT

chmod +x /tmp/synapse_db_config.sh

# Ejecutar el script dentro de un contenedor temporal
docker run --rm \
    -v chatsender_synapse_data:/data \
    -v /tmp/synapse_db_config.sh:/configure.sh \
    -e DB_PASSWORD="${DB_PASSWORD}" \
    alpine:latest sh /configure.sh

# Limpiar
rm /tmp/synapse_db_config.sh

echo ""
echo "========================================="
echo "Configuración completada"
echo "========================================="
echo ""
echo "Reinicia el contenedor de Synapse:"
echo "  docker-compose restart synapse"
echo ""
