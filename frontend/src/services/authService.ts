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
  // Constante para timeout de 5 minutos (en milisegundos)
  private readonly SESSION_TIMEOUT: number = 5 * 60 * 1000;
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

      // 5. Guardar token, llave privada y timestamp de actividad
      this.token = token;
      localStorage.setItem('authToken', token);
      this.updateActivity(); // Marcar inicio de sesión como actividad
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
    localStorage.removeItem('lastActive');
    cryptoService.clearKeys();
  }

  /**
   * Verifica si hay una sesión activa y válida (no expirada)
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('authToken');
    if (!token) return false;

    // Verificar timeout de inactividad
    const lastActiveStr = localStorage.getItem('lastActive');
    if (lastActiveStr) {
      const lastActive = parseInt(lastActiveStr, 10);
      const now = Date.now();

      if (now - lastActive > this.SESSION_TIMEOUT) {
        console.log('Sesión expirada por inactividad');
        this.logout();
        return false;
      }
    }

    return true;
  }

  /**
   * Actualiza el timestamp de última actividad
   */
  updateActivity(): void {
    if (this.token || localStorage.getItem('authToken')) {
      localStorage.setItem('lastActive', Date.now().toString());
    }
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
