"""
Modelos de sesión para rastrear usuarios temporales en Synapse
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from datetime import datetime
import uuid

# Importar Base desde auth.py para compartir la misma metadata
from models.auth import Base


class Session(Base):
    """
    Tabla de sesiones de chat activas.
    Relaciona llaves autorizadas con usuarios temporales de Synapse.
    """
    __tablename__ = "sessions"
    
    # UUID único de la sesión
    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Referencia a la llave pública del usuario
    public_key = Column(String(512), ForeignKey('authorized_keys.public_key'), nullable=False, index=True)
    
    # ID del usuario creado en Synapse (formato: @username:server_name)
    synapse_user_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Alias temporal generado para esta sesión
    alias = Column(String(255), nullable=False)
    
    # Timestamp de inicio de sesión
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Timestamp de última actividad
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Si la sesión está activa
    is_active = Column(Boolean, default=True, nullable=False)

    # Token de acceso de Synapse (para evitar login repetido y rate limits)
    access_token = Column(String(512), nullable=True)

    def __repr__(self):
        return f"<Session(session_id={self.session_id}, alias={self.alias}, active={self.is_active})>"
