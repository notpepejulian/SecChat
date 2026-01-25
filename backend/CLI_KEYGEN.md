#  Generador de Pares de Llaves - Documentación

## Descripción
CLI para generar y gestionar pares de llaves Ed25519 para autenticación en ChatSender.

## Características
-  Genera pares de llaves Ed25519 (pública/privada)
-  Registra llaves públicas en la base de datos
-  Lista llaves autorizadas
-  Revoca llaves por prefijo
-  Soporte para Docker y ejecución local
-  Manejo robusto de errores de conexión

## Uso

### Con Docker (Recomendado)

Desde la raíz del proyecto, usa el script auxiliar:

```bash
# Mostrar ayuda
./keygen.sh help

# Generar 1 par de llaves
./keygen.sh generate

# Generar 3 pares de llaves
./keygen.sh generate 3

# Listar todas las llaves
./keygen.sh list

# Revocar una llave (usando prefijo)
./keygen.sh revoke ABC123
```

O ejecuta directamente en el contenedor:

```bash
docker exec -it chatsender_backend python cli_keygen.py generate 3
```

### Ejecución Local

Si tienes MariaDB/MySQL corriendo localmente:

```bash
# Asegúrate de que DB_HOST="localhost" en el .env
python backend/cli_keygen.py generate 3
```

## Comandos

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `generate [n]` | Genera n pares de llaves (default: 1) | `generate 5` |
| `list` | Lista todas las llaves autorizadas | `list` |
| `revoke <prefix>` | Revoca una llave usando su prefijo | `revoke ABC123` |
| `help` | Muestra ayuda | `help` |

## Flujo de Trabajo

1. **Generar llaves**:
   ```bash
   ./keygen.sh generate 1
   ```
   
   Output:
   ```
    Generando 1 par(es) de llaves...
   
    Par de llaves #1 generado:
      Llave Pública:  Base64EncodedPublicKey...
      Llave Privada:  Base64EncodedPrivateKey...
      Estado: Registrada y activa
   
        IMPORTANTE: Guarda la llave privada de forma segura.
   ```

2. **Distribuir la llave privada**: Envía la llave privada al usuario de forma segura (nunca por canales inseguros).

3. **Verificar llaves activas**:
   ```bash
   ./keygen.sh list
   ```

4. **Revocar una llave** (si es necesario):
   ```bash
   ./keygen.sh revoke XYZ789
   ```

## Seguridad

 **IMPORTANTE**:
- Las llaves privadas **NO** se guardan en el servidor
- Solo las llaves públicas se registran en la base de datos
- Distribuye las llaves privadas por canales seguros
- Revoca llaves comprometidas inmediatamente
- Usa `generate` con moderación (solo cuando necesites nuevos usuarios)

## Arquitectura

```
Cliente                    Servidor
--------                   ---------
Llave Privada  ------>     Verifica con Llave Pública (BD)
(firmada)                  (AuthorizedKey)
```

## Troubleshooting

### Error: "Can't connect to MySQL server"

**Solución**: 
- Si usas Docker, asegúrate de ejecutar el comando **dentro** del contenedor
- Usa el script `./keygen.sh` que maneja esto automáticamente
- O ejecuta: `docker exec -it chatsender_backend python cli_keygen.py [comando]`

### Error: "DB_PASSWORD no está configurada"

**Solución**:
- Verifica que el archivo `.env` existe en la raíz del proyecto
- Asegúrate de que contiene `DB_PASSWORD=...`

### Error: El contenedor no existe

**Solución**:
```bash
# Inicia los servicios
docker compose up -d
```

## Dependencias

- `cryptography` - Para generación de llaves Ed25519
- `sqlalchemy` - ORM para base de datos
- `pymysql` - Driver de MySQL
- `python-dotenv` - Carga de variables de entorno

## Integración

El sistema de autenticación funciona con:
1. **Challenge-Response**: El servidor envía un desafío aleatorio
2. **Firma Digital**: El cliente firma el desafío con su llave privada
3. **Verificación**: El servidor verifica la firma usando la llave pública registrada

Ver `services/crypto_service.py` para la implementación completa.
