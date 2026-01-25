import os
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text, Column, Integer, or_
from sqlalchemy.orm import Session, sessionmaker
import httpx # Cliente HTTP asíncrono para interactuar con Synapse

# Scheduler para tareas automáticas
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Importar servicios y modelos propios
from services.auth_service import AuthService
from services.synapse_service import SynapseService
from services.cleanup_service import CleanupService
from services.alias_service import AliasService
from models.auth import Base, AuthorizedKey
from models.session import Session as ChatSession

from services.crypto_service import CryptoService
from datetime import datetime, timedelta


# ====================================================================
# 1. CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ====================================================================

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL_ENV = os.getenv("DATABASE_URL")

if DATABASE_URL_ENV:
    DATABASE_URL = DATABASE_URL_ENV
else:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}"

# -----------------
# Configuración Synapse (Matrix)
# -----------------
SYNAPSE_BASE_URL = "http://synapse:8008"

# ====================================================================
# 2. CONFIGURACIÓN DE LA BASE DE DATOS (SQLAlchemy)
# ====================================================================

# Crea el motor de la base de datos. pool_recycle es importante para MySQL.
engine = create_engine(
    DATABASE_URL,
    echo=True, # Para mostrar logs SQL en la consola
    pool_pre_ping=True,
    pool_recycle=3600
)

# Sesión local para interactuar con la db
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Función de dependencia de FastAPI para obtener una sesión de DB.
    Garantiza que la sesión se cierre después de cada solicitud.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ====================================================================
# 3. CONFIGURACIÓN DEL CLIENTE SYNAPSE (httpx)
# ====================================================================

# Usamos un AsyncContextManager para manejar la creación y cierre
# del cliente HTTP asíncrono de manera segura.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función que se ejecuta al iniciar y al detener la aplicación.
    Inicializa el cliente HTTP global y el scheduler para tareas automáticas.
    """
    global synapse_client, scheduler
    
    # Inicializar cliente HTTP
    synapse_client = httpx.AsyncClient(base_url=SYNAPSE_BASE_URL, timeout=10.0)
    print(f"✅ Cliente Synapse inicializado con URL base: {SYNAPSE_BASE_URL}")
    
    # Inicializar scheduler para tareas automáticas
    scheduler = AsyncIOScheduler()
    
    # Configurar tareas periódicas de limpieza
    session_timeout = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    
    # Cada hora: Limpieza de llaves expiradas
    scheduler.add_job(
        cleanup_expired_keys_task,
        trigger=IntervalTrigger(hours=1),
        id="cleanup_expired_keys",
        name="Limpieza de llaves expiradas",
        replace_existing=True
    )
    
    # Cada 30 minutos: Limpieza de sesiones inactivas
    scheduler.add_job(
        cleanup_inactive_sessions_task,
        trigger=IntervalTrigger(minutes=30),
        args=[session_timeout],
        id="cleanup_inactive_sessions",
        name="Limpieza de sesiones inactivas",
        replace_existing=True
    )
    
    # Cada día: Limpieza de usuarios huérfanos de Synapse
    scheduler.add_job(
        cleanup_orphaned_users_task,
        trigger=IntervalTrigger(days=1),
        id="cleanup_orphaned_users",
        name="Limpieza de usuarios huérfanos",
        replace_existing=True
    )
    
    # Iniciar scheduler
    scheduler.start()
    print("✅ Scheduler de limpieza automática iniciado")
    print(f"   - Llaves expiradas: cada hora")
    print(f"   - Sesiones inactivas (>{session_timeout}min): cada 30 min")
    print(f"   - Usuarios huérfanos: cada día")
    
    yield  # Aquí se ejecuta la aplicación
    
    # Shutdown: detener scheduler y cerrar cliente
    scheduler.shutdown()
    await synapse_client.aclose()
    print("✅ Scheduler detenido y cliente Synapse cerrado.")


# Tareas de limpieza para el scheduler
async def cleanup_expired_keys_task():
    """Tarea programada: elimina llaves expiradas"""
    db = SessionLocal()
    try:
        await CleanupService.cleanup_expired_keys(db)
    finally:
        db.close()

async def cleanup_inactive_sessions_task(timeout_minutes: int):
    """Tarea programada: elimina sesiones inactivas"""
    db = SessionLocal()
    try:
        await CleanupService.cleanup_inactive_sessions(db, synapse_client, timeout_minutes)
    finally:
        db.close()

async def cleanup_orphaned_users_task():
    """Tarea programada: elimina usuarios huérfanos de Synapse"""
    db = SessionLocal()
    try:
        await CleanupService.cleanup_orphaned_synapse_users(db, synapse_client)
    finally:
        db.close()


# Inicialización de la aplicación FastAPI
app = FastAPI(lifespan=lifespan, title="Servicio Backend ChatSender")

# Configurar CORS para permitir peticiones del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir al dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas en la base de datos al iniciar
Base.metadata.create_all(bind=engine)

# ====================================================================
# 4. MODELOS DE DATOS (Pydantic)
# ====================================================================

class ChallengeRequest(BaseModel):
    """Solicitud de challenge para autenticación"""
    public_key: str

class ChallengeResponse(BaseModel):
    """Respuesta con challenge"""
    challenge: str

class VerifyRequest(BaseModel):
    """Solicitud de verificación de challenge"""
    public_key: str
    signature: str

class VerifyResponse(BaseModel):
    """Respuesta de verificación exitosa"""
    token: str
    message: str

class KeyGenRequest(BaseModel):
    """Solicitud para generar par de llaves exitosa"""
    count: int = 1

class RevokeKeyRequest(BaseModel):
    """Solicitud para eliminar llaves exitosa"""
    public_key: str

class SessionStartResponse(BaseModel):
    """Respuesta al iniciar sesión de chat"""
    session_id: str
    synapse_user_id: str
    synapse_password: str
    alias: str
    server_name: str
    message: str

class SessionInfoResponse(BaseModel):
    """Información de sesión activa"""
    session_id: str
    alias: str
    synapse_user_id: str
    created_at: str
    last_activity: str
    is_active: bool

class SessionEndRequest(BaseModel):
    """Solicitud para terminar sesión"""
    session_id: str

class UserLookupRequest(BaseModel):
    """Solicitud para buscar usuario por alias o llave pública"""
    query: str

class UserLookupResponse(BaseModel):
    """Respuesta de búsqueda de usuario"""
    found: bool
    synapse_user_id: Optional[str] = None
    alias: Optional[str] = None
    public_key: Optional[str] = None
    message: Optional[str] = None


# ====================================================================
# 5. ENDPOINTS DE LA API
# ====================================================================

# --- Endpoint de Prueba General ---
@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    """Verifica que el servicio esté corriendo."""
    return {"message": "El servicio Backend (FastAPI) está operativo y listo para servir."}

# --- Endpoint de HealthCheck ---
@app.get("/health", status_code=status.HTTP_200_OK)
async def read_health():
    """Verifica que el servicio esté healthy."""
    return {"message": "El servicio Backend (FastAPI) está healthy."}

# ====================================================================
# ENDPOINTS DE AUTENTICACIÓN
# ====================================================================

@app.post("/auth/challenge", response_model=ChallengeResponse)
def request_challenge(request: ChallengeRequest, db: Session = Depends(get_db)):
    """
    Solicita un challenge para autenticación.

    Args:
        request: Contiene la llave pública del usuario

    Returns:
        Challenge aleatorio que debe ser firmado con la llave privada
    """
    challenge = AuthService.request_challenge(request.public_key, db)

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Llave pública no autorizada o inactiva"
        )

    return ChallengeResponse(challenge=challenge)

@app.post("/auth/verify", response_model=VerifyResponse)
def verify_challenge(request: VerifyRequest, db: Session = Depends(get_db)):
    """
    Verifica la firma del challenge y genera un JWT token.

    Args:
        request: Contiene la llave pública y la firma del challenge

    Returns:
        JWT token para acceso autenticado
    """
    token = AuthService.verify_challenge_response(
        public_key=request.public_key,
        signature=request.signature,
        db=db
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma inválida o challenge expirado"
        )

    return VerifyResponse(
        token=token,
        message="Autenticación exitosa"
    )

# --- Endpoint de Prueba de Conexión a DB ---
@app.get("/db-status")
def check_db_connection(db: Session = Depends(get_db)):
    """Verifica la conexión con la base de datos MariaDB."""
    try:
        # Ejecutar una consulta simple para verificar la conexión
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Conexión con MariaDB exitosa."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la conexión a la base de datos: {e}"
        )

# --- Endpoint de Prueba de Conexión a Synapse ---
@app.get("/synapse-version")
async def get_synapse_version():
    """
    Llama al endpoint público '/_matrix/client/versions' de Synapse
    para verificar la comunicación.
    """
    try:
        # matrix-nio no es necesario para esta simple llamada, usamos httpx
        response = await synapse_client.get("/_matrix/client/versions")
        response.raise_for_status() # Lanza una excepción para códigos de error HTTP
        
        return {
            "status": "ok",
            "synapse_data": response.json()
        }
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudo conectar con el servicio Synapse en {SYNAPSE_BASE_URL}. ¿Está levantado el contenedor?"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al comunicarse con Synapse: {e}"
        )

@app.post("/keys/generate")
def generate_keys(request: KeyGenRequest, db: Session = Depends(get_db)):
    """
    Genera pares de llaves (privada/pública) y almacena solo la pública en la BD.
    Similar al script cli_keygen.py.
    """
    try:
        keys_output = []
        
        # Configurar expiración (7 días por defecto)
        expiration_days = int(os.getenv("KEY_EXPIRATION_DAYS", "7"))

        for _ in range(request.count):
            # Genera llave privada y pública
            private_key, public_key = CryptoService.generate_keypair()
            
            # Calcular fecha de expiración
            now = datetime.utcnow()
            expires_at = now + timedelta(days=expiration_days)

            # Guarda solo la pública en la base de datos
            new_key = AuthorizedKey(
                public_key=public_key,
                created_at=now,
                expires_at=expires_at,
                is_active=True
            )
            db.add(new_key)
            db.commit()

            keys_output.append({
                "public_key": public_key,
                "private_key": private_key,
                "expires_at": expires_at.isoformat()
            })

        return {
            "success": True,
            "generated": len(keys_output),
            "keys": keys_output
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error generando llaves: {e}"
        )

@app.post("/keys/revoke")
def revoke_key(request: RevokeKeyRequest, db: Session = Depends(get_db)):
    """
    Elimina una llave pública de la base de datos.
    Usado para revocar completamente una sesión o dispositivo.
    """
    try:
        key = db.query(AuthorizedKey).filter(
            AuthorizedKey.public_key == request.public_key
        ).first()

        if not key:
            raise HTTPException(
                status_code=404,
                detail="La llave pública no existe o ya fue eliminada."
            )

        # 1. Eliminar sesiones asociadas primero (para evitar error FK)
        db.query(ChatSession).filter(
            ChatSession.public_key == request.public_key
        ).delete()
        
        # 2. Eliminar la llave
        db.delete(key)
        db.commit()

        return {
            "success": True,
            "message": "Llave eliminada correctamente.",
            "public_key": request.public_key
        }

    except Exception as e:
        db.rollback()
        print(f"Error en revoke_key: {str(e)}") # Log para debug
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando la llave: {e}"
        )

@app.get("/keys/list")
def list_keys(db: Session = Depends(get_db)):
    """
    Lista todas las llaves públicas almacenadas en la base de datos.
    Incluye estado y fecha de creación.
    """
    try:
        keys = db.query(AuthorizedKey).all()

        return {
            "success": True,
            "count": len(keys),
            "keys": [
                {
                    "public_key": key.public_key,
                    "is_active": key.is_active,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": key.expires_at.isoformat() if hasattr(key, 'expires_at') and key.expires_at else None
                }
                for key in keys
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listando llaves: {e}"
        )

# ====================================================================
# ENDPOINTS DE SESIÓN (USUARIOS TEMPORALES)
# ====================================================================

def get_current_user(authorization: str = Header(None)) -> str:
    """
    Dependency para verificar JWT token y obtener public_key del usuario.
    
    Args:
        authorization: Header Authorization con formato "Bearer <token>"
        
    Returns:
        public_key del usuario autenticado
        
    Raises:
        HTTPException si el token es inválido o falta
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido"
        )
    
    token = authorization.replace("Bearer ", "")
    public_key = AuthService.verify_jwt(token)
    
    if not public_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    
    return public_key

@app.post("/session/start", response_model=SessionStartResponse)
async def start_session(
    db: Session = Depends(get_db),
    public_key: str = Depends(get_current_user)
):
    """
    Inicia una sesión de chat temporal.
    Si ya existe una sesión activa, la reutiliza.
    Crea usuario temporal en Synapse si es necesario.
    
    Requiere: JWT token válido
    """
    try:
        # 1. Verificar si ya existe una sesión activa para esta llave
        existing_session = db.query(ChatSession).filter(
            ChatSession.public_key == public_key,
            ChatSession.is_active == True
        ).first()

        if existing_session:
            # Si tiene access_token, podemos reutilizarla directamente
            if existing_session.access_token:
                print(f"♻️ Reutilizando sesión existente: {existing_session.session_id}")
                return SessionStartResponse(
                    session_id=existing_session.session_id,
                    synapse_user_id=existing_session.synapse_user_id,
                    alias=existing_session.alias,
                    server_name=SynapseService.SYNAPSE_SERVER_NAME,
                    access_token=existing_session.access_token,
                    message="Sesión recuperada correctamente"
                )
            else:
                # Si existe pero no tiene token (versión anterior), la desactivamos y creamos una nueva
                print(f"⚠️ Sesión existente sin token, desactivando: {existing_session.session_id}")
                existing_session.is_active = False
                db.commit()

        # 2. Crear nueva sesión
        session_id = str(__import__('uuid').uuid4())
        alias = AliasService.generate_alias(public_key, session_id)
        
        # Crear usuario temporal en Synapse
        synapse_user = await SynapseService.create_temporary_user(
            public_key, session_id, synapse_client
        )
        
        if not synapse_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear usuario temporal en Synapse"
            )
        
        # 3. Loguear usuario inmediatamente para obtener access_token
        login_data = await SynapseService.login_user(
            synapse_user["user_id"],
            synapse_user["password"],
            synapse_client
        )
        
        access_token = login_data["access_token"] if login_data else None
        
        if not access_token:
            print("⚠️ No se pudo obtener access_token tras creación de usuario")

        # Crear registro de sesión en BD
        new_session = ChatSession(
            session_id=session_id,
            public_key=public_key,
            synapse_user_id=synapse_user["user_id"],
            alias=alias,
            access_token=access_token,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            is_active=True
        )
        
        db.add(new_session)
        db.commit()
        
        return SessionStartResponse(
            session_id=session_id,
            synapse_user_id=synapse_user["user_id"],
            synapse_password=synapse_user["password"],
            access_token=access_token,
            alias=alias,
            server_name=SynapseService.SYNAPSE_SERVER_NAME,
            message="Sesión iniciada correctamente"
        )
        
    except Exception as e:
        db.rollback()
        print(f"Error start_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar sesión: {e}"
        )

@app.get("/session/info", response_model=SessionInfoResponse)
def get_session_info(
    db: Session = Depends(get_db),
    public_key: str = Depends(get_current_user)
):
    """
    Obtiene información de la sesión activa del usuario.
    
    Requiere: JWT token válido
    """
    try:
        # Buscar sesión activa por public_key
        session = db.query(ChatSession).filter(
            ChatSession.public_key == public_key,
            ChatSession.is_active == True
        ).order_by(ChatSession.created_at.desc()).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay sesión activa"
            )
        
        # Actualizar última actividad
        session.last_activity = datetime.utcnow()
        db.commit()
        
        return SessionInfoResponse(
            session_id=session.session_id,
            alias=session.alias,
            synapse_user_id=session.synapse_user_id,
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            is_active=session.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener información de sesión: {e}"
        )

@app.post("/session/end")
async def end_session(
    request: SessionEndRequest,
    db: Session = Depends(get_db),
    public_key: str = Depends(get_current_user)
):
    """
    Termina una sesión de chat y elimina usuario de Synapse.
    
    Requiere: JWT token válido
    """
    try:
        # Buscar sesión
        session = db.query(ChatSession).filter(
            ChatSession.session_id == request.session_id,
            ChatSession.public_key == public_key,
            ChatSession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada o ya terminada"
            )
        
        # Eliminar usuario de Synapse
        deleted = await SynapseService.delete_user(
            session.synapse_user_id,
            synapse_client
        )
        
        if not deleted:
            print(f"⚠️ No se pudo eliminar usuario de Synapse: {session.synapse_user_id}")
        
        # Marcar sesión como inactiva
        session.is_active = False
        db.commit()
        
        return {
            "success": True,
            "message": "Sesión terminada correctamente",
            "session_id": request.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al terminar sesión: {e}"
        )

@app.get("/admin/cleanup")
async def trigger_cleanup(db: Session = Depends(get_db)):
    """
    Trigger manual de limpieza completa (solo para administradores).
    En producción debería requerir autenticación de admin.
    """
    try:
        session_timeout = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
        
        stats = await CleanupService.run_full_cleanup(
            db, synapse_client, session_timeout
        )
        
        return {
            "success": True,
            "message": "Limpieza completada",
            "stats": stats
        }
        
    except Exception as e:
        print(f"Error en cleanup manual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar limpieza: {e}"
        )

@app.post("/users/lookup", response_model=UserLookupResponse)
def lookup_user(
    request: UserLookupRequest,
    db: Session = Depends(get_db),
    # current_user: str = Depends(get_current_user) # Opcional: requerir auth
):
    """
    Busca un usuario activo por su Alias Temporal o Llave Pública.
    Retorna el ID de usuario de Synapse para iniciar chat.
    """
    try:
        query = request.query.strip()
        
        # Buscar en sesiones activas
        session = db.query(ChatSession).filter(
            ChatSession.is_active == True,
            or_(
                ChatSession.alias == query,
                ChatSession.public_key == query,
                ChatSession.synapse_user_id == query
            )
        ).order_by(ChatSession.last_activity.desc()).first()
        
        if not session:
            return UserLookupResponse(
                found=False,
                message="Usuario no encontrado o no está conectado."
            )
            
        return UserLookupResponse(
            found=True,
            synapse_user_id=session.synapse_user_id,
            alias=session.alias,
            public_key=session.public_key
        )

    except Exception as e:
        print(f"Error en lookup_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error buscando usuario: {e}"
        )

# --- Ejemplo de Función para Registrar un Usuario (ADMIN API) ---
# Nota: Esta función es solo un esqueleto. Necesitarás autenticación de administrador
# y habilitar la API de registro de administración en Synapse.
async def register_user_on_synapse(username: str, password: str, display_name: str):
    """
    Esqueleto para registrar un usuario usando la API de administración de Synapse.
    Requiere un token de acceso de administrador (ACCESS_TOKEN).
    """
    ADMIN_API_PATH = "/_synapse/admin/v1/register"
    ADMIN_ACCESS_TOKEN = "tu_token_de_admin_aqui" # ¡NO USAR EN PRODUCCIÓN!

    payload = {
        "username": username,
        "password": password,
        "display_name": display_name,
        "admin": False
    }
    headers = {
        "Authorization": f"Bearer {ADMIN_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = await synapse_client.post(
            ADMIN_API_PATH,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Manejar errores como el usuario ya existe, token inválido, etc.
        print(f"Fallo al registrar usuario: {e}")
        return {"error": str(e)}