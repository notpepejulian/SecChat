/**
 * Servicio de autenticación con el backend
 */
import { cryptoService } from './cryptoService';

const API_URL = '/api';

export interface AuthResponse {
  success: boolean;
  token?: string;
  challenge?: string;
  error?: string;
}

class AuthService {
  private token: string | null = null;

  /**
   * Inicia sesión con llave privada
   */
  async login(privateKey: string): Promise<AuthResponse> {
    try {
      // 1. Derivar llave pública de la privada
      const publicKey = await this.getPublicKeyFromPrivate(privateKey);

      // 2. Solicitar challenge
      const challengeResponse = await fetch(`${API_URL}/auth/challenge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ public_key: publicKey })
      });

      if (!challengeResponse.ok) {
        return { success: false, error: 'Llave no autorizada' };
      }

      const { challenge } = await challengeResponse.json();

      // 3. Firmar challenge con llave privada
      const signature = await cryptoService.signMessage(challenge, privateKey);

      // 4. Enviar firma para verificación
      const verifyResponse = await fetch(`${API_URL}/auth/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          public_key: publicKey,
          signature: signature
        })
      });

      if (!verifyResponse.ok) {
        return { success: false, error: 'Firma inválida' };
      }

      const { token } = await verifyResponse.json();

      // 5. Guardar token y llave privada
      this.token = token;
      localStorage.setItem('authToken', token);
      cryptoService.savePrivateKey(privateKey, ''); // TODO: password

      return { success: true, token };
    } catch (error) {
      console.error('Login error:', error);

      // Mensaje de error más específico
      let errorMessage = 'Error de conexión';

      if (error instanceof Error) {
        if (error.message.includes('Ed25519') || error.message.includes('subtle')) {
          errorMessage = 'Tu navegador no soporta Ed25519. Usa Chrome/Safari actualizado.';
        } else if (error.message.includes('firmar')) {
          errorMessage = error.message;
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
          errorMessage = 'No se puede conectar al servidor. Verifica tu conexión.';
        } else {
          errorMessage = error.message;
        }
      }

      return { success: false, error: errorMessage };
    }
  }

  /**
   * Cierra sesión
   */
  logout(): void {
    this.token = null;
    localStorage.removeItem('authToken');
    cryptoService.clearKeys();
  }

  /**
   * Verifica si hay una sesión activa
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('authToken');
    return token !== null;
  }

  /**
   * Obtiene el token actual
   */
  getToken(): string | null {
    if (this.token) return this.token;
    return localStorage.getItem('authToken');
  }

  /**
   * Deriva llave pública de llave privada (simulado)
   * En realidad, el usuario debe tener ambas llaves del backend
   */
  private async getPublicKeyFromPrivate(privateKey: string): Promise<string> {
    // Por ahora, asumimos que el usuario tiene la llave pública separada
    // y la guardamos cuando hace login
    const storedPublicKey = localStorage.getItem('publicKey');
    if (storedPublicKey) {
      return storedPublicKey;
    }

    // Si no existe, debemos pedirla al usuario
    throw new Error('Public key not found. User must provide both keys.');
  }

  /**
   * Guarda la llave pública del usuario
   */
  setPublicKey(publicKey: string): void {
    localStorage.setItem('publicKey', publicKey);
  }

  /**
   * Obtiene la llave pública guardada
   */
  getPublicKey(): string | null {
    return localStorage.getItem('publicKey');
  }
}

export const authService = new AuthService();
