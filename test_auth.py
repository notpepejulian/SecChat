#!/usr/bin/env python3
"""
Script de prueba para el flujo de autenticación.
Uso: python test_auth.py <public_key> <private_key>
"""
import sys
import requests
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def test_auth(public_key, private_key):
    """Prueba el flujo completo de autenticación"""
    
    BASE_URL = "http://localhost/api"
    
    print("Test de Autenticación\n")
    print(f"Llave Pública:  {public_key}")
    print(f"Llave Privada:  {private_key}\n")
    
    # Paso 1: Solicitar challenge
    print("Paso 1: Solicitando challenge...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/challenge",
            json={"public_key": public_key}
        )
        response.raise_for_status()
        data = response.json()
        challenge = data["challenge"]
        print(f"Challenge recibido: {challenge}\n")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"   Detalles: {e.response.json().get('detail')}\n")
            return False
        else:
            print(f"Error HTTP: {e}\n")
            return False
    except Exception as e:
        print(f"Error de conexión: {e}\n")
        return False
    
    # Paso 2: Firmar el challenge
    print("Paso 2: Firmando challenge con llave privada...")
    try:
        # Decodificar llave privada
        private_bytes = base64.b64decode(private_key)
        private_key_obj = Ed25519PrivateKey.from_private_bytes(private_bytes)
        
        # Firmar challenge
        challenge_bytes = challenge.encode('utf-8')
        signature = private_key_obj.sign(challenge_bytes)
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        print(f"Challenge firmado\n")
    except Exception as e:
        print(f"Error al firmar: {e}\n")
        return False
    
    # Paso 3: Verificar firma y obtener token
    print("Paso 3: Enviando firma para verificación...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/verify",
            json={
                "public_key": public_key,
                "signature": signature_b64
            }
        )
        response.raise_for_status()
        data = response.json()
        token = data["token"]
        message = data["message"]
        
        print(f"{message}")
        print(f"Token JWT: {token[:50]}...\n")
        print("=" * 60)
        print("AUTENTICACIÓN EXITOSA")
        print("=" * 60)
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"Error en verificación: {e}")
        print(f"   Detalles: {e.response.json().get('detail')}\n")
        return False
    except Exception as e:
        print(f"Error: {e}\n")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python test_auth.py <public_key> <private_key>")
        print("\nEjemplo:")
        print("  python test_auth.py 'NiV4e3GCL8ApElivG7LYytnlGsmx9zngkMtaHrCbC9o=' 'Kz1+KXWKaEYwwlOrKk8JY9k5qO7v/cgrP/gxJIv5U9g='")
        sys.exit(1)
    
    public_key = sys.argv[1]
    private_key = sys.argv[2]
    
    success = test_auth(public_key, private_key)
    sys.exit(0 if success else 1)
