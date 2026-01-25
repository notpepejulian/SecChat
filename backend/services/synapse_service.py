"""
Servicio para interactuar con Synapse Admin API.
Gestiona usuarios temporales en el servidor Matrix.
"""
import hashlib
import secrets
import os
from typing import Optional, Dict
import httpx
from datetime import datetime


class SynapseService:
    """Servicio para gestión de usuarios temporales en Synapse"""
    
    # Configuración de Synapse
    SYNAPSE_BASE_URL = os.getenv("SYNAPSE_BASE_URL", "http://synapse:8008")
    SYNAPSE_SERVER_NAME = os.getenv("SYNAPSE_SERVER_NAME", "fed.local")
    SYNAPSE_ADMIN_TOKEN = os.getenv("SYNAPSE_ADMIN_TOKEN", "")
    
    @classmethod
    async def create_temporary_user(
        cls,
        public_key: str,
        session_id: str,
        client: httpx.AsyncClient
    ) -> Optional[Dict]:
        """
        Crea un usuario temporal en Synapse.
        
        Args:
            public_key: Llave pública del usuario (para generar username único)
            session_id: ID de la sesión
            client: Cliente HTTP asíncrono
            
        Returns:
            Dict con user_id, password y displayname si exitoso, None si falla
        """
        # Generar username único basado en hash de public_key + session_id + timestamp
        username = cls._generate_username(public_key, session_id)
        
        # Generar password temporal aleatorio
        password = secrets.token_urlsafe(32)
        
        # Displayname temporal
        displayname = f"TempUser_{username[:8]}"
        
        # Preparar payload para Admin API
        payload = {
            "password": password,
            "displayname": displayname,
            "admin": False,
            "deactivated": False
        }
        
        headers = {
            "Authorization": f"Bearer {cls.SYNAPSE_ADMIN_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            # Endpoint de Admin API para crear usuarios
            # https://matrix-org.github.io/synapse/latest/admin_api/user_admin_api.html
            endpoint = f"/_synapse/admin/v2/users/@{username}:{cls.SYNAPSE_SERVER_NAME}"
            
            response = await client.put(
                f"{cls.SYNAPSE_BASE_URL}{endpoint}",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "user_id": f"@{username}:{cls.SYNAPSE_SERVER_NAME}",
                "username": username,
                "password": password,
                "displayname": displayname,
                "synapse_response": data
            }
            
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP al crear usuario en Synapse: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Error al crear usuario en Synapse: {e}")
            return None
    
    @classmethod
    async def delete_user(
        cls,
        user_id: str,
        client: httpx.AsyncClient
    ) -> bool:
        """
        Elimina un usuario de Synapse (deactivate).
        
        Args:
            user_id: ID completo del usuario (ej: @user:server.com)
            client: Cliente HTTP asíncrono
            
        Returns:
            True si exitoso, False si falla
        """
        headers = {
            "Authorization": f"Bearer {cls.SYNAPSE_ADMIN_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "deactivated": True,
            "erase": True  # Elimina datos del usuario
        }
        
        try:
            # Endpoint para desactivar usuarios
            endpoint = f"/_synapse/admin/v2/users/{user_id}"
            
            response = await client.put(
                f"{cls.SYNAPSE_BASE_URL}{endpoint}",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            
            response.raise_for_status()
            return True
            
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP al eliminar usuario en Synapse: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            print(f"Error al eliminar usuario en Synapse: {e}")
            return False
    
    @classmethod
    async def get_user_info(
        cls,
        user_id: str,
        client: httpx.AsyncClient
    ) -> Optional[Dict]:
        """
        Obtiene información de un usuario de Synapse.
        
        Args:
            user_id: ID completo del usuario
            client: Cliente HTTP asíncrono
            
        Returns:
            Dict con información del usuario si existe, None si no
        """
        headers = {
            "Authorization": f"Bearer {cls.SYNAPSE_ADMIN_TOKEN}"
        }
        
        try:
            endpoint = f"/_synapse/admin/v2/users/{user_id}"
            
            response = await client.get(
                f"{cls.SYNAPSE_BASE_URL}{endpoint}",
                headers=headers,
                timeout=10.0
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            print(f"Error HTTP al obtener info de usuario: {e.response.status_code}")
            return None
        except Exception as e:
            print(f"Error al obtener info de usuario: {e}")
            return None
    
    @classmethod
    async def login_user(
        cls,
        user_id: str,
        password: str,
        client: httpx.AsyncClient
    ) -> Optional[Dict]:
        """
        Loguea un usuario en Synapse para obtener access_token.
        """
        try:
            payload = {
                "type": "m.login.password",
                "identifier": {
                    "type": "m.id.user",
                    "user": user_id
                },
                "password": password
            }
            
            response = await client.post(
                f"{cls.SYNAPSE_BASE_URL}/_matrix/client/v3/login",
                json=payload,
                timeout=10.0
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP login Synapse: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Error login Synapse: {e}")
            return None

    @staticmethod
    def _generate_username(public_key: str, session_id: str) -> str:
        """
        Genera un username único basado en hash.
        
        Args:
            public_key: Llave pública del usuario
            session_id: ID de la sesión
            
        Returns:
            Username único (solo alfanumérico lowercase)
        """
        # Crear hash único
        timestamp = str(datetime.utcnow().timestamp())
        hash_input = f"{public_key}{session_id}{timestamp}"
        hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Tomar primeros 16 caracteres del hash
        username = f"temp_{hash_digest[:16]}"
        
        return username.lower()
