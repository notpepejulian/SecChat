/**
 * Servicio para manejar la comunicación con Matrix (Synapse)
 * Utiliza matrix-js-sdk para conectarse al servidor Matrix
 */

import * as sdk from 'matrix-js-sdk';

export interface MatrixCredentials {
    userId: string;
    password: string;
    deviceId?: string;
    accessToken?: string;
}

export interface SessionInfo {
    sessionId: string;
    synapseUserId: string;
    synapsePassword: string;
    accessToken?: string;
    alias: string;
    serverName: string;
}

class MatrixService {
    private client: any = null;
    // Usar el origen actual (ej: http://192.168.1.166) ya que Nginx proxea /_matrix a Synapse
    // Evitar puerto 8008 directo que suele estar bloqueado
    private baseUrl: string = window.location.origin;
    private sessionInfo: SessionInfo | null = null;
    private messageCallbacks: Array<(roomId: string, event: any) => void> = [];
    private roomUpdateCallbacks: Array<(room: any) => void> = [];

    /**
     * Inicia sesión en Matrix con las credenciales proporcionadas
     */
    async login(credentials: MatrixCredentials): Promise<void> {
        try {
            this.client = sdk.createClient({
                baseUrl: this.baseUrl,
                userId: credentials.userId,
                deviceId: credentials.deviceId,
            });

            // Registrar listeners (ahora incluye auto-join)
            this.registerQueuedListeners();

            // Usar login explícito con estructura de identificador v3
            const response = await this.client.login('m.login.password', {
                identifier: {
                    type: 'm.id.user',
                    user: credentials.userId
                },
                password: credentials.password
            });

            console.log('✅ Conectado a Matrix:', response);

            // Iniciar sincronización
            await this.client.startClient({ initialSyncLimit: 10 });

            // Esperar a que esté listo
            await this.waitForSyncPrepared();

            // Revisar de nuevo por si se pasó algo
            this.processExistingInvites();

        } catch (error) {
            console.error('❌ Error al conectar con Matrix:', error);
            throw error;
        }
    }

    /**
     * Espera a que el cliente Matrix esté sincronizado
     */
    private async waitForSyncPrepared(): Promise<void> {
        if (this.client.isInitialSyncComplete()) return;

        console.log('⏳ Esperando sincronización inicial de Matrix...');
        return new Promise((resolve) => {
            const onSync = (state: string) => {
                console.log(`🔄 Matrix Sync State: ${state}`);
                if (state === 'PREPARED' || state === 'SYNCING') {
                    if (this.client.isInitialSyncComplete()) {
                        console.log('✅ Cliente Matrix sincronizado y preparado');
                        this.client.removeListener('sync', onSync);
                        resolve();
                    }
                }
            };
            this.client.on('sync', onSync);
        });
    }

    /**
     * Inicia una nueva sesión de chat en el backend
     */
    async startSession(jwtToken: string): Promise<SessionInfo> {
        try {
            const response = await fetch('/api/session/start', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${jwtToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Error al iniciar sesión: ${response.statusText}`);
            }

            const rawData = await response.json();

            const data: SessionInfo = {
                sessionId: rawData.session_id,
                synapseUserId: rawData.synapse_user_id,
                synapsePassword: rawData.synapse_password,
                accessToken: rawData.access_token,
                alias: rawData.alias,
                serverName: rawData.server_name || 'fed.local'
            };

            this.sessionInfo = data;

            console.log('📦 Info de sesión (Matrix):', {
                user: data.synapseUserId,
                hasToken: !!data.accessToken,
                alias: data.alias
            });

            if (data.accessToken && data.synapseUserId) {
                console.log('🔑 Usando Access Token para conectar...');
                this.client = sdk.createClient({
                    baseUrl: this.baseUrl,
                    accessToken: data.accessToken,
                    userId: data.synapseUserId
                });

                // Registrar listeners (ahora incluye auto-join)
                this.registerQueuedListeners();

                // Iniciar sincronización
                this.client.startClient({ initialSyncLimit: 10 });

                // Esperar sincronización
                await this.waitForSyncPrepared();

                // Revisar de nuevo por si se pasó algo
                this.processExistingInvites();

                console.log('✅ Matrix client started with Token!');

            } else if (data.synapseUserId && data.synapsePassword) {
                console.log('🔑 Usando Password para conectar (fallback)...');
                await this.login({
                    userId: data.synapseUserId,
                    password: data.synapsePassword
                });
            } else {
                throw new Error("No se recibieron credenciales válidas");
            }

            return data;

        } catch (error) {
            console.error('❌ Error al iniciar sesión:', error);
            throw error;
        }
    }

    /**
     * Termina la sesión actual
     */
    async endSession(jwtToken: string, sessionId: string): Promise<void> {
        try {
            if (this.client) {
                this.client.stopClient();
                this.client = null;
            }

            await fetch('/api/session/end', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${jwtToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            this.sessionInfo = null;

        } catch (error) {
            console.error('❌ Error al terminar sesión:', error);
            throw error;
        }
    }

    /**
     * Crea una sala privada (DM) con otro usuario
     */
    async createDirectMessage(recipientUserId: string): Promise<string> {
        if (!this.client) {
            throw new Error('Cliente Matrix no inicializado');
        }

        try {
            const room = await this.client.createRoom({
                visibility: 'private',
                is_direct: true,
                invite: [recipientUserId],
                preset: 'trusted_private_chat'
            });

            console.log('✅ Sala creada:', room.room_id);

            let retryCount = 0;
            while (!this.client.getRoom(room.room_id) && retryCount < 10) {
                await new Promise(r => setTimeout(r, 500));
                retryCount++;
            }

            return room.room_id;

        } catch (error) {
            console.error('❌ Error al crear sala:', error);
            throw error;
        }
    }

    /**
     * Envía un mensaje a una sala
     */
    async sendMessage(roomId: string, message: string): Promise<void> {
        if (!this.client) {
            throw new Error('Cliente Matrix no inicializado');
        }

        try {
            await this.client.sendTextMessage(roomId, message);
            console.log('✅ Mensaje enviado');

        } catch (error) {
            console.error('❌ Error al enviar mensaje:', error);
            throw error;
        }
    }

    /**
     * Registra en el cliente Matrix todos los callbacks que fueron encolados
     */
    private registerQueuedListeners(): void {
        if (!this.client) return;

        console.log(`📡 Registrando ${this.messageCallbacks.length} listeners de mensajes y ${this.roomUpdateCallbacks.length} de salas`);

        this.client.on('Room.timeline', (event: any, room: any) => {
            if (event.getType() !== 'm.room.message') return;

            const senderId = event.getSender();
            console.log(`📩 [MatrixJS] Evento en ${room.roomId} de ${senderId}:`, event.getContent().body);

            if (senderId === this.client.getUserId()) return;

            this.messageCallbacks.forEach(cb => cb(room.roomId, event));
        });

        this.client.on('Room', (room: any) => {
            console.log(`🏠 [MatrixJS] Nueva sala o actualización: ${room.roomId}`);
            this.checkAndJoinRoom(room);
            this.roomUpdateCallbacks.forEach(cb => cb(room));
        });

        this.client.on('Room.membership', (event: any, member: any) => {
            const myUserId = this.client.getUserId();

            if (member.userId === myUserId) {
                console.log(`👤 [MatrixJS] Tu membresía en ${member.roomId} cambió a: ${member.membership}`);

                if (member.membership === 'invite') {
                    console.log(`📩 [MatrixJS] Invitación detectada para ${member.roomId}. Uniéndose...`);
                    this.client.joinRoom(member.roomId).then(() => {
                        console.log(`✅ [MatrixJS] Unido correctamente a ${member.roomId}`);
                    }).catch((err: any) => {
                        console.error(`❌ [MatrixJS] Error al unirse a ${member.roomId}:`, err);
                    });
                }

                if (member.membership === 'join') {
                    const room = this.client.getRoom(member.roomId);
                    if (room) this.roomUpdateCallbacks.forEach(cb => cb(room));
                }
            }
        });
    }

    /**
     * Verifica si estamos invitados a una sala y se une
     */
    private checkAndJoinRoom(room: any): void {
        const myUserId = this.client.getUserId();
        const myMember = room.getMember(myUserId);

        if (myMember && myMember.membership === 'invite') {
            console.log(`🤝 [MatrixJS] Uniéndose a sala invitada (check): ${room.roomId}`);
            this.client.joinRoom(room.roomId).catch((err: any) => {
                console.error(`❌ [MatrixJS] Fallo al unirse a ${room.roomId}:`, err);
            });
        }
    }

    /**
     * Procesa todas las salas actuales buscando invitaciones
     */
    private processExistingInvites(): void {
        if (!this.client) return;
        const rooms = this.client.getRooms();
        console.log(`🔍 Revisando ${rooms.length} salas por invitaciones...`);
        rooms.forEach((room: any) => this.checkAndJoinRoom(room));
    }

    onMessage(callback: (roomId: string, event: any) => void): void {
        this.messageCallbacks.push(callback);
    }

    onRoomUpdate(callback: (room: any) => void): void {
        this.roomUpdateCallbacks.push(callback);
    }

    getRooms(): any[] {
        if (!this.client) return [];
        return this.client.getRooms();
    }

    getRoomTimeline(roomId: string): any[] {
        if (!this.client) return [];
        const room = this.client.getRoom(roomId);
        if (!room) return [];
        return room.timeline;
    }

    getCurrentUserId(): string | null {
        if (!this.client) return null;
        return this.client.getUserId();
    }

    getCurrentAlias(): string | null {
        return this.sessionInfo?.alias || null;
    }

    isConnected(): boolean {
        return this.client !== null && this.client.isInitialSyncComplete();
    }
}

export const matrixService = new MatrixService();
