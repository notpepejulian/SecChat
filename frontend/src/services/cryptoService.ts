
import * as nacl from 'tweetnacl';
import * as naclUtil from 'tweetnacl-util';

/**
 * Servicio de criptografía usando TweetNaCl (Pure JS)
 * Compatible con Ed25519 para firmas digitales
 * Funciona en contextos no seguros (HTTP)
 */

export interface KeyPair {
  publicKey: string;  // Base64
  privateKey: string; // Base64
}

class CryptoService {
  /**
   * Genera un par de llaves Ed25519
   */
  async generateKeyPair(): Promise<KeyPair> {
    const keyPair = nacl.sign.keyPair();

    const publicKeyBase64 = naclUtil.encodeBase64(keyPair.publicKey);
    const privateKeyBase64 = naclUtil.encodeBase64(keyPair.secretKey);

    return {
      publicKey: publicKeyBase64,
      privateKey: privateKeyBase64
    };
  }

  /**
   * Firma un mensaje con la llave privada
   */
  async signMessage(message: string, privateKeyBase64: string): Promise<string> {
    try {
      let privateKey = naclUtil.decodeBase64(privateKeyBase64);

      // Adaptation: Handle 32-byte seeds (from Backend) vs 64-byte secret keys (TweetNaCl native)
      if (privateKey.length === 32) {
        // Derive full 64-byte key pair from seed
        const keyPair = nacl.sign.keyPair.fromSeed(privateKey);
        privateKey = keyPair.secretKey;
      } else if (privateKey.length !== nacl.sign.secretKeyLength) {
        console.error(`Invalid key length: ${privateKey.length}. Expected 32 (seed) or ${nacl.sign.secretKeyLength} (full).`);
        throw new Error("Formato de llave inválido. Las llaves deben ser de 32 bytes (seed) o 64 bytes (full).");
      }

      const messageBytes = naclUtil.decodeUTF8(message);

      const signature = nacl.sign.detached(messageBytes, privateKey);

      return naclUtil.encodeBase64(signature);
    } catch (error: any) {
      console.error("Error signing message:", error);
      if (error.message.includes("Formato de llave")) {
        throw error;
      }
      throw new Error("No se pudo firmar el mensaje. Verifica que la llave privada sea válida.");
    }
  }

  /**
   * Verifica una firma digital
   */
  async verifySignature(
    message: string,
    signatureBase64: string,
    publicKeyBase64: string
  ): Promise<boolean> {
    try {
      const publicKey = naclUtil.decodeBase64(publicKeyBase64);
      const signature = naclUtil.decodeBase64(signatureBase64);
      const messageBytes = naclUtil.decodeUTF8(message);

      return nacl.sign.detached.verify(messageBytes, signature, publicKey);
    } catch (error) {
      console.error("Error verifying signature:", error);
      return false;
    }
  }

  /**
   * Guarda llave privada en localStorage
   */
  savePrivateKey(privateKey: string, password: string): void {
    // Nota: en una app real debería encriptarse con el password
    localStorage.setItem('privateKey', privateKey);
  }

  /**
   * Recupera llave privada de localStorage
   */
  getPrivateKey(): string | null {
    return localStorage.getItem('privateKey');
  }

  /**
   * Limpia llaves del localStorage
   */
  clearKeys(): void {
    localStorage.removeItem('privateKey');
    // localStorage.removeItem('publicKey'); // Si se usa
  }
}

export const cryptoService = new CryptoService();
