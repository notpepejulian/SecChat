#!/usr/bin/env python3
"""
CLI para generar y gestionar llaves autorizadas.
Uso: python cli_keygen.py [comando]
"""
import sys
import os
from pathlib import Path

# Agregar el directorio backend al path para imports correctos
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.crypto_service import CryptoService
from models.auth import AuthorizedKey, Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
env_path = backend_dir.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Configuración de base de datos
DB_USER = os.getenv("DB_USER", "synapse_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "synapse")

if not DB_PASSWORD:
    print("\n Error: DB_PASSWORD no está configurada.")
    print("   Asegúrate de que el archivo .env existe y contiene DB_PASSWORD.\n")
    sys.exit(1)

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}"


def init_db():
    """Inicializa la base de datos y crea tablas"""
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        # Verificar conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
    except OperationalError as e:
        print(f"\n Error de conexión a la base de datos:")
        print(f"   {str(e)}\n")
        print(" Soluciones posibles:")
        print("   1. Si usas Docker: ejecuta este script dentro del contenedor backend:")
        print("      docker exec -it chatsender_backend python cli_keygen.py [comando]\n")
        print("   2. Si usas local: asegúrate de que MariaDB/MySQL esté corriendo y")
        print("      que DB_HOST en .env apunte a 'localhost' (no 'db')\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n Error inesperado al inicializar la base de datos:")
        print(f"   {str(e)}\n")
        sys.exit(1)


def generate_key(count=1):
    """Genera nuevas llaves y las registra en la BD"""
    session = init_db()
    
    print(f"\n Generando {count} par(es) de llaves...\n")
    
    # Configurar expiración (7 días por defecto)
    expiration_days = int(os.getenv("KEY_EXPIRATION_DAYS", "7"))
    
    for i in range(count):
        # Generar par de llaves
        private_key, public_key = CryptoService.generate_keypair()
        
        # Calcular fecha de expiración
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expiration_days)
        
        # Registrar llave pública en la BD
        authorized_key = AuthorizedKey(
            public_key=public_key,
            created_at=now,
            expires_at=expires_at,
            is_active=True
        )
        
        session.add(authorized_key)
        session.commit()
        
        print(f" Par de llaves #{i+1} generado:")
        print(f"   Llave Pública:  {public_key}")
        print(f"   Llave Privada:  {private_key}")
        print(f"   Estado: Registrada y activa")
        print(f"   Expira en: {expiration_days} días ({expires_at.strftime('%Y-%m-%d %H:%M')} UTC)\n")
        print(f"     IMPORTANTE: Guarda la llave privada de forma segura.")
        print(f"   La llave privada NO se guarda en el servidor.\n")
        print("-" * 80)
    
    session.close()
    print(f"\n {count} llave(s) generada(s) y registrada(s) exitosamente.\n")


def list_keys():
    """Lista todas las llaves autorizadas"""
    session = init_db()
    
    keys = session.query(AuthorizedKey).all()
    
    if not keys:
        print("\n  No hay llaves autorizadas registradas.\n")
        return
    
    print(f"\n📋 Llaves autorizadas ({len(keys)}):\n")
    
    for key in keys:
        # Verificar estado
        if key.is_expired:
            status = "⏰ Expirada"
        elif key.is_active:
            status = "🟢 Activa"
        else:
            status = "🔴 Revocada"
        
        last_used = key.last_used.strftime("%Y-%m-%d %H:%M") if key.last_used else "Nunca"
        expires_at = key.expires_at.strftime("%Y-%m-%d %H:%M") if hasattr(key, 'expires_at') and key.expires_at else "N/A"
        
        print(f"  {status}")
        print(f"  Llave: {key.public_key[:32]}...")
        print(f"  Creada: {key.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Expira: {expires_at}")
        print(f"  Último uso: {last_used}")
        print("-" * 80)
    
    session.close()


def revoke_key(public_key_prefix):
    """Revoca una llave autorizada"""
    session = init_db()
    
    # Buscar llave por prefijo
    keys = session.query(AuthorizedKey).filter(
        AuthorizedKey.public_key.like(f"{public_key_prefix}%")
    ).all()
    
    if not keys:
        print(f"\n No se encontró ninguna llave con el prefijo: {public_key_prefix}\n")
        return
    
    if len(keys) > 1:
        print(f"\n  Se encontraron {len(keys)} llaves con ese prefijo. Sé más específico.\n")
        return
    
    key = keys[0]
    key.is_active = False
    session.commit()
    
    print(f"\n Llave revocada: {key.public_key[:32]}...\n")
    
    session.close()


def show_help():
    """Muestra ayuda"""
    print("""
 CLI de Gestión de Llaves - ChatSender

Comandos disponibles:

  generate [n]     Genera n pares de llaves (default: 1)
  list             Lista todas las llaves autorizadas
  revoke <prefix>  Revoca una llave por su prefijo
  help             Muestra esta ayuda

Ejemplos:

    Con Docker (recomendado):
    docker exec -it chatsender_backend python cli_keygen.py generate 3
    docker exec -it chatsender_backend python cli_keygen.py list
    docker exec -it chatsender_backend python cli_keygen.py revoke ABC123

    Local:
    python backend/cli_keygen.py generate 3
    python backend/cli_keygen.py list
    python backend/cli_keygen.py revoke ABC123

  IMPORTANTE:
   - Las llaves privadas NO se guardan en el servidor.
   - Distribúyelas de forma segura a los usuarios autorizados.
   - Si usas Docker, ejecuta los comandos dentro del contenedor backend.
    """)


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "generate":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        generate_key(count)
    
    elif command == "list":
        list_keys()
    
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("\n Debes especificar el prefijo de la llave a revocar.\n")
            return
        revoke_key(sys.argv[2])
    
    elif command == "help":
        show_help()
    
    else:
        print(f"\n Comando desconocido: {command}\n")
        show_help()


if __name__ == "__main__":
    main()
