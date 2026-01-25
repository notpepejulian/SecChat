"""
Servicio de limpieza automática de datos temporales.
Elimina llaves expiradas, sesiones inactivas y usuarios de Synapse.
"""
from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.auth import AuthorizedKey
from models.session import Session as ChatSession
from services.synapse_service import SynapseService
import httpx


class CleanupService:
    """Servicio para limpieza automática de datos temporales"""
    
    @staticmethod
    async def cleanup_expired_keys(db: Session) -> int:
        """
        Elimina llaves expiradas de la base de datos.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Número de llaves eliminadas
        """
        try:
            # Buscar llaves expiradas
            expired_keys = db.query(AuthorizedKey).filter(
                AuthorizedKey.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_keys)
            
            # Eliminar llaves expiradas
            for key in expired_keys:
                db.delete(key)
            
            db.commit()
            
            if count > 0:
                print(f"✅ Limpieza: {count} llave(s) expirada(s) eliminada(s)")
            
            return count
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error al limpiar llaves expiradas: {e}")
            return 0
    
    @staticmethod
    async def cleanup_inactive_sessions(
        db: Session,
        client: httpx.AsyncClient,
        timeout_minutes: int = 60
    ) -> int:
        """
        Elimina sesiones inactivas y sus usuarios de Synapse.
        
        Args:
            db: Sesión de base de datos
            client: Cliente HTTP para Synapse API
            timeout_minutes: Minutos de inactividad antes de eliminar
            
        Returns:
            Número de sesiones eliminadas
        """
        try:
            timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            # Buscar sesiones inactivas
            inactive_sessions = db.query(ChatSession).filter(
                ChatSession.is_active == True,
                ChatSession.last_activity < timeout_threshold
            ).all()
            
            count = 0
            
            for session in inactive_sessions:
                # Eliminar usuario de Synapse
                deleted = await SynapseService.delete_user(
                    session.synapse_user_id,
                    client
                )
                
                if deleted:
                    # Marcar sesión como inactiva
                    session.is_active = False
                    count += 1
                else:
                    print(f"⚠️ No se pudo eliminar usuario Synapse: {session.synapse_user_id}")
            
            db.commit()
            
            if count > 0:
                print(f"✅ Limpieza: {count} sesión(es) inactiva(s) eliminada(s)")
            
            return count
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error al limpiar sesiones inactivas: {e}")
            return 0
    
    @staticmethod
    async def cleanup_orphaned_synapse_users(
        db: Session,
        client: httpx.AsyncClient
    ) -> int:
        """
        Elimina usuarios de Synapse sin sesión activa.
        
        Args:
            db: Sesión de base de datos
            client: Cliente HTTP para Synapse API
            
        Returns:
            Número de usuarios eliminados
        """
        try:
            # Buscar sesiones marcadas como inactivas
            inactive_sessions = db.query(ChatSession).filter(
                ChatSession.is_active == False
            ).all()
            
            count = 0
            
            for session in inactive_sessions:
                # Verificar que el usuario aún exista en Synapse
                user_info = await SynapseService.get_user_info(
                    session.synapse_user_id,
                    client
                )
                
                if user_info and not user_info.get('deactivated', False):
                    # Usuario existe y no está desactivado, eliminarlo
                    deleted = await SynapseService.delete_user(
                        session.synapse_user_id,
                        client
                    )
                    
                    if deleted:
                        count += 1
                
                # Eliminar registro de sesión de la BD
                db.delete(session)
            
            db.commit()
            
            if count > 0:
                print(f"✅ Limpieza: {count} usuario(s) huérfano(s) de Synapse eliminado(s)")
            
            return count
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error al limpiar usuarios huérfanos: {e}")
            return 0
    
    @staticmethod
    async def run_full_cleanup(
        db: Session,
        client: httpx.AsyncClient,
        session_timeout_minutes: int = 60
    ) -> dict:
        """
        Ejecuta todas las tareas de limpieza.
        
        Args:
            db: Sesión de base de datos
            client: Cliente HTTP para Synapse API
            session_timeout_minutes: Minutos de inactividad para sesiones
            
        Returns:
            Dict con estadísticas de limpieza
        """
        print("🧹 Iniciando limpieza automática...")
        
        keys_cleaned = await CleanupService.cleanup_expired_keys(db)
        sessions_cleaned = await CleanupService.cleanup_inactive_sessions(
            db, client, session_timeout_minutes
        )
        orphans_cleaned = await CleanupService.cleanup_orphaned_synapse_users(
            db, client
        )
        
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "expired_keys_removed": keys_cleaned,
            "inactive_sessions_removed": sessions_cleaned,
            "orphaned_users_removed": orphans_cleaned,
            "total_cleaned": keys_cleaned + sessions_cleaned + orphans_cleaned
        }
        
        print(f"✅ Limpieza completada: {stats['total_cleaned']} elementos eliminados")
        
        return stats
