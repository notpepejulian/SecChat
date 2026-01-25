#!/usr/bin/env python3
"""
Script para configurar automáticamente Synapse con MariaDB
"""
import os
import re
import subprocess

# Leer variables de entorno del archivo .env
env_vars = {}
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
except FileNotFoundError:
    print("⚠️ No se encontró el archivo .env, usando valores por defecto")

DB_USER = env_vars.get('DB_USER', 'synapse_user')
DB_PASSWORD = env_vars.get('DB_PASSWORD', '')
DB_NAME = env_vars.get('DB_NAME', 'synapse')




print("⏳ Generando nueva configuración base con Synapse (para recuperar secretos y estructura)...")

# 1. Generar configuración en contenedor temporal
# Usamos un directorio temporal en el contenedor
try:
    # Ejecutar generate
    # Usamos server_name fed.local como estaba antes
    cmd = [
        'docker', 'run', '--rm', 
        '-e', 'SYNAPSE_SERVER_NAME=fed.local',
        '-e', 'SYNAPSE_REPORT_STATS=no',
        'matrixdotorg/synapse:develop', 
        'generate'
    ]
    # No montamos volumen aún, solo queremos que genere en stdout o en un archivo efímero que podamos leer?
    # El comando generate escribe en /data/homeserver.yaml por defecto.
    # Vamos a montarle un volumen anonimo o usar stdout si fuera posible, pero generate escribe archivo.
    # Mejor: run con volumen temporal, luego cat.
    
    # generate command exits 0 if success
    # Pero necesitamos el contenido.
    # Hagamos un truco: generar y cat en el mismo run no se puede facil.
    # Usemos un contenedor que haga generate y luego cat.
    
    subprocess.run(
        'docker run --rm --entrypoint sh matrixdotorg/synapse:develop -c "python3 -m synapse.app.homeserver --server-name fed.local --config-path /tmp/homeserver.yaml --generate-config --report-stats=no >/dev/null 2>&1 && cat /tmp/homeserver.yaml"',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True
    )
    # Wait, capture output needs to be assigned
    result = subprocess.run(
         'docker run --rm --entrypoint sh matrixdotorg/synapse:develop -c "python3 -m synapse.app.homeserver --server-name fed.local --config-path /tmp/homeserver.yaml --generate-config --report-stats=no >/dev/null && cat /tmp/homeserver.yaml"',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Error generando config: {result.stderr}")
        exit(1)
        
    content = result.stdout
    print("✅ Configuración base generada exitosamente.")

except Exception as e:
    print(f"❌ Excepción generando config: {e}")
    exit(1)

# 2. Asegurar SQLite y Corregir Paths
print("ℹ️ Corrigiendo paths para usar volumen /data...")

# Reemplazar paths absolutos o relativos incorrectos
# media_store_path: /media_store -> /data/media_store
if 'media_store_path: /media_store' in content:
    content = content.replace('media_store_path: /media_store', 'media_store_path: /data/media_store')
elif 'media_store_path: media_store' in content:
    content = content.replace('media_store_path: media_store', 'media_store_path: /data/media_store')

# uploads_path? (a veces está)
content = content.replace('uploads_path: /uploads', 'uploads_path: /data/uploads')
content = content.replace('uploads_path: uploads', 'uploads_path: /data/uploads')

# signing_key_path
content = content.replace('signing_key_path: /', 'signing_key_path: /data/')
# Si es relativo (ej: "fed.local.signing.key")
# Buscamos 'signing_key_path: "fed.local.signing.key"'
content = re.sub(r'signing_key_path: ["\']?([^/]+)["\']?$', r'signing_key_path: "/data/\1"', content, flags=re.MULTILINE)

# log_config
content = re.sub(r'log_config: ["\']?([^/]+)["\']?$', r'log_config: "/data/\1"', content, flags=re.MULTILINE)

# pid_file
content = content.replace('pid_file: /homeserver.pid', 'pid_file: /data/homeserver.pid')
content = content.replace('pid_file: homeserver.pid', 'pid_file: /data/homeserver.pid')

# database sqlite path if generated differently
content = content.replace('database: /homeserver.db', 'database: /data/homeserver.db')
content = content.replace('database: homeserver.db', 'database: /data/homeserver.db')


# Verificaciones extra
if 'name: sqlite3' not in content:
    print("⚠️ La configuración generada no parece usar sqlite3. Forzando...")
    # (Lógica simple de reemplazo si fuera necesario, pero generate suele usar sqlite)
else:
    print("ℹ️ Configuración usa SQLite correctamente.")

# 3. Escribir al volumen REAL
print(f"⏳ Escribiendo configuración válida al volumen chatsender_synapse_data...")

try:
    process = subprocess.Popen(
        ['docker', 'run', '--rm', '-i', '-v', 'chatsender_synapse_data:/data', 'alpine', 'sh', '-c', 'cat > /data/homeserver.yaml'],
        stdin=subprocess.PIPE,
        text=True
    )
    process.communicate(input=content)
    
    if process.returncode == 0:
        print("✅ Synapse re-configurado y reparado exitosamente")
    else:
        print("❌ Error al escribir configuración")
        exit(1)

except Exception as e:
    print(f"❌ Error escribiendo archivo: {e}")
    exit(1)


