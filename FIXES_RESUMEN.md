#  Resumen de Correcciones - Generador de Llaves

## Problemas Encontrados y Solucionados

### 1.  Error de Conexión a Base de Datos
**Problema**: El CLI `cli_keygen.py` intentaba conectarse a `localhost` cuando Docker usa el host `db`.

**Solución**:
-  Agregado soporte para cargar variables de entorno desde `.env`
-  Agregado manejo robusto de errores de conexión con mensajes claros
-  Agregado import del módulo `text` de SQLAlchemy para queries SQL
-  Verificación de conexión antes de crear tablas

### 2.  Endpoints de Autenticación Faltantes
**Problema**: El backend no tenía implementados los endpoints `/auth/challenge` y `/auth/verify`.

**Solución**:
-  Agregados endpoints POST `/auth/challenge` y `/auth/verify`
-  Configurado CORS para permitir peticiones del frontend
-  Creación automática de tablas en la base de datos al iniciar
-  Modelos Pydantic para validación de requests

### 3.  Incompatibilidad de Formatos de Llaves
**Problema**: El backend genera llaves en formato **raw bytes** (Ed25519) pero el frontend esperaba formato **JWK**.

**Solución**:
-  Modificado `cryptoService.ts` para soportar llaves raw del backend
-  Agregada función `wrapEd25519PrivateKey()` que convierte raw bytes a PKCS#8
-  Fallback a formato JWK para compatibilidad con llaves antiguas
-  Mejor manejo de errores con mensajes descriptivos

### 4.  Dependencia Faltante
**Problema**: El contenedor backend no tenía instalado `PyJWT`.

**Solución**:
-  Reconstruida la imagen del backend con todas las dependencias

## Archivos Modificados

### Backend
1. **`backend/cli_keygen.py`**
   - Carga de `.env` con `python-dotenv`
   - Manejo robusto de errores de conexión
   - Mensajes de ayuda mejorados con instrucciones Docker

2. **`backend/main.py`**
   - Endpoints `/auth/challenge` y `/auth/verify`
   - Configuración CORS
   - Creación automática de tablas
   - Modelos Pydantic para requests

### Frontend
3. **`frontend/src/services/cryptoService.ts`**
   - Soporte para llaves Ed25519 raw (formato del backend)
   - Conversión PKCS#8 para Web Crypto API
   - Mejor manejo de errores

### Nuevos Archivos
4. **`keygen.sh`**
   - Script wrapper para ejecutar CLI desde fuera del contenedor
   - Verificaciones de Docker
   - Inicio automático de contenedor si está detenido

5. **`test_auth.py`**
   - Script de prueba del flujo completo de autenticación
   - Útil para debugging

6. **`backend/CLI_KEYGEN.md`**
   - Documentación completa del CLI
   - Guía de uso
   - Troubleshooting
   - Ejemplos

## Uso Correcto

### Generar Llaves (con Docker)

```bash
# Desde la raíz del proyecto
./keygen.sh generate 1
```

Output esperado:
```
 Generando 1 par(es) de llaves...

 Par de llaves #1 generado:
   Llave Pública:  NiV4e3GCL8ApElivG7LYytnlGsmx9zngkMtaHrCbC9o=
   Llave Privada:  Kz1+KXWKaEYwwlOrKk8JY9k5qO7v/cgrP/gxJIv5U9g=
   Estado: Registrada y activa
```

### Usar las Llaves en el Frontend

1. Accede a http://localhost/login
2. Pega la **Llave Pública** en el primer campo
3. Pega la **Llave Privada** en el segundo campo
4. Click en "Desencriptar y Entrar"

El sistema ahora:
1.  Solicita un challenge al backend
2.  Firma el challenge localmente con la llave privada
3.  Envía la firma al backend para verificación
4.  Recibe un JWT token válido
5.  Redirige a `/chat`

## Flujo de Autenticación

```
┌─────────────┐                           ┌──────────────┐
│  Frontend   │                           │   Backend    │
│  (Browser)  │                           │  (FastAPI)   │
└──────┬──────┘                           └──────┬───────┘
       │                                          │
       │  POST /auth/challenge                    │
       │  { public_key: "ABC..." }                │
       ├─────────────────────────────────────────>│
       │                                          │
       │                                          │ Verifica llave
       │                                          │ en BD (activa?)
       │                                          │
       │  { challenge: "XYZ..." }                 │
       │<─────────────────────────────────────────┤
       │                                          │
       │  [Firma challenge localmente]            │
       │   con llave privada                      │
       │                                          │
       │  POST /auth/verify                       │
       │  { public_key, signature }               │
       ├─────────────────────────────────────────>│
       │                                          │
       │                                          │ Verifica firma
       │                                          │ con llave pública
       │                                          │
       │  { token: "JWT...", message: "..." }     │
       │<─────────────────────────────────────────┤
       │                                          │
       │  Autenticado ✓                           │
       │                                          │
```

## Verificación

Para verificar que todo funciona:

```bash
# 1. Generar llaves
./keygen.sh generate 1

# 2. Copiar las llaves del output

# 3. Probar autenticación desde línea de comandos
python3 test_auth.py 'LLAVE_PUBLICA' 'LLAVE_PRIVADA'

# 4. Si el test pasa, probar en el navegador
# Ir a http://localhost/login
```

## Troubleshooting

### "Llave no autorizada" en frontend
-  Verificar que la llave pública esté registrada: `./keygen.sh list`
-  Verificar que la llave esté activa ( no )
-  Verificar que estés pegando la llave pública correcta

### "Error de conexión"
-  Verificar que Docker esté corriendo: `docker ps`
-  Verificar que el backend esté healthy: `docker compose ps`
-  Ver logs: `docker compose logs backend`

### "Firma inválida"
-  Verificar que la llave privada corresponda a la pública
-  Verificar que no haya espacios o saltos de línea en las llaves
-  Limpiar caché del navegador

## Seguridad

 **IMPORTANTE**:
- Las llaves privadas se procesan **solo en el navegador**, nunca se envían al servidor
- Solo la llave pública se almacena en la base de datos
- La firma se hace localmente usando Web Crypto API
- El servidor solo verifica la firma, nunca ve la llave privada

## Próximos Pasos

Para mejorar el sistema:

1. [ ] Encriptar llaves privadas en localStorage con password del usuario
2. [ ] Agregar 2FA opcional
3. [ ] Implementar rotación de llaves
4. [ ] Agregar logs de auditoría
5. [ ] Implementar rate limiting en endpoints de auth
