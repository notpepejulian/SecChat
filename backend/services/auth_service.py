"""
Servicio de autenticación basado en criptografía de llave pública.
Usa challenge-response para verificar posesión de llave privada.
"""
import jwt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from models.auth import AuthorizedKey
from services.crypto_service import CryptoService


class AuthService:
    """Servicio de autenticación"""
    
    # Secret para JWT (en producción debe venir de variable de entorno)
    JWT_SECRET = "your-secret-key-change-in-production"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # Cache de challenges activos (public_key -> challenge)
    _active_challenges: Dict[str, tuple] = {}
    
    @classmethod
    def request_challenge(cls, public_key: str, db: Session) -> Optional[str]:
        """
        Solicita un challenge para autenticación.
        
        Args:
            public_key: Llave pública del usuario
            db: Sesión de base de datos
            
        Returns:
            Optional[str]: Challenge si la llave está autorizada y válida, None si no
        """
        # Verificar que la llave pública está autorizada y no expirada
        authorized_key = db.query(AuthorizedKey).filter(
            AuthorizedKey.public_key == public_key,
            AuthorizedKey.is_active == True
        ).first()
        
        if not authorized_key:
            return None
        
        # Verificar que no ha expirado
        if authorized_key.is_expired:
            return None
        
        # Generar challenge
        challenge = CryptoService.create_challenge()
        
        # Guardar en cache con timestamp (válido por 5 minutos)
        expiration = time.time() + 300  # 5 minutos
        cls._active_challenges[public_key] = (challenge, expiration)
        
        return challenge
    
    @classmethod
    def verify_challenge_response(
        cls,
        public_key: str,
        signature: str,
        db: Session
    ) -> Optional[str]:
        """
        Verifica la respuesta al challenge y genera JWT.
        
        Args:
            public_key: Llave pública del usuario
            signature: Firma del challenge con llave privada
            db: Sesión de base de datos
            
        Returns:
            Optional[str]: JWT token si la verificación es exitosa, None si no
        """
        # Verificar que existe un challenge activo
        if public_key not in cls._active_challenges:
            return None
        
        challenge, expiration = cls._active_challenges[public_key]
        
        # Verificar que no ha expirado
        if time.time() > expiration:
            del cls._active_challenges[public_key]
            return None
        
        # Verificar firma
        is_valid = CryptoService.verify_signature(
            message=challenge,
            signature_b64=signature,
            public_key_b64=public_key
        )
        
        if not is_valid:
            return None
        
        # Limpiar challenge usado
        del cls._active_challenges[public_key]
        
        # Actualizar última actividad
        authorized_key = db.query(AuthorizedKey).filter(
            AuthorizedKey.public_key == public_key
        ).first()
        
        if authorized_key:
            authorized_key.last_used = datetime.utcnow()
            db.commit()
        
        # Generar JWT
        token = cls._generate_jwt(public_key)
        
        return token
    
    @classmethod
    def _generate_jwt(cls, public_key: str) -> str:
        """
        Genera un JWT token.
        
        Args:
            public_key: Llave pública del usuario
            
        Returns:
            str: JWT token
        """
        payload = {
            "sub": public_key,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=cls.JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(payload, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)
        
        return token
    
    @classmethod
    def verify_jwt(cls, token: str) -> Optional[str]:
        """
        Verifica un JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Optional[str]: Llave pública si el token es válido, None si no
        """
        try:
            payload = jwt.decode(token, cls.JWT_SECRET, algorithms=[cls.JWT_ALGORITHM])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @classmethod
    def cleanup_expired_challenges(cls):
        """Limpia challenges expirados del cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, exp) in cls._active_challenges.items()
            if current_time > exp
        ]
        
        for key in expired_keys:
            del cls._active_challenges[key]
