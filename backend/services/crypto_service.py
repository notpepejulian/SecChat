"""
Servicio de criptografía para el sistema de mensajería anónima.
Maneja generación de llaves, firma digital y verificación.
"""
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from typing import Tuple, Optional


class CryptoService:
    """Servicio para operaciones criptográficas"""
    
    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """
        Genera un par de llaves Ed25519 (pública/privada).
        
        Returns:
            Tuple[str, str]: (private_key_base64, public_key_base64)
        """
        # Generar llave privada
        private_key = Ed25519PrivateKey.generate()
        
        # Serializar llave privada a bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Obtener llave pública
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Codificar en base64
        private_b64 = base64.b64encode(private_bytes).decode('utf-8')
        public_b64 = base64.b64encode(public_bytes).decode('utf-8')
        
        return private_b64, public_b64
    
    @staticmethod
    def sign_message(message: str, private_key_b64: str) -> str:
        """
        Firma un mensaje con una llave privada Ed25519.
        
        Args:
            message: Mensaje a firmar
            private_key_b64: Llave privada en base64
            
        Returns:
            str: Firma digital en base64
        """
        # Decodificar llave privada
        private_bytes = base64.b64decode(private_key_b64)
        private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
        
        # Firmar mensaje
        message_bytes = message.encode('utf-8')
        signature = private_key.sign(message_bytes)
        
        # Codificar firma en base64
        return base64.b64encode(signature).decode('utf-8')
    
    @staticmethod
    def verify_signature(message: str, signature_b64: str, public_key_b64: str) -> bool:
        """
        Verifica una firma digital.
        
        Args:
            message: Mensaje original
            signature_b64: Firma en base64
            public_key_b64: Llave pública en base64
            
        Returns:
            bool: True si la firma es válida
        """
        try:
            # Decodificar llave pública
            public_bytes = base64.b64decode(public_key_b64)
            public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
            
            # Decodificar firma
            signature = base64.b64decode(signature_b64)
            
            # Verificar
            message_bytes = message.encode('utf-8')
            public_key.verify(signature, message_bytes)
            
            return True
        except (InvalidSignature, Exception):
            return False
    
    @staticmethod
    def create_challenge() -> str:
        """
        Crea un challenge aleatorio para autenticación.
        
        Returns:
            str: Challenge en base64
        """
        import secrets
        challenge_bytes = secrets.token_bytes(32)
        return base64.b64encode(challenge_bytes).decode('utf-8')
