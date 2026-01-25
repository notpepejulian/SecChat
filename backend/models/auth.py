"""
Modelos de autenticación para el sistema de mensajería anónima
"""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()


class AuthorizedKey(Base):
    """
    Tabla de llaves públicas autorizadas.
    Solo usuarios con llave pública registrada pueden acceder.
    No se guardan perfiles ni información personal.
    """
    __tablename__ = "authorized_keys"
    
    # Llave pública Ed25519 en formato base64 (identificador único)
    public_key = Column(String(512), primary_key=True, index=True)
    
    # Timestamp de creación (solo para auditoría)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Timestamp de expiración (7 días desde creación por defecto)
    expires_at = Column(DateTime, nullable=False)
    
    # Si está activa o revocada
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamp de última actividad (opcional, para limpieza)
    last_used = Column(DateTime, nullable=True)
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la llave ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<AuthorizedKey(public_key={self.public_key[:16]}...)>"
