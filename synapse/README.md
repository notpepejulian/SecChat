# Synapse Setup - Guía de Inicialización

Este directorio contiene la lógica necesaria para configurar y administrar el servidor de mensajería Matrix (Synapse). Para que el sistema **SecChat** funcione, Synapse debe estar correctamente inicializado y vinculado con el Backend mediante un Token de Administrador.

## Pre-requisitos

1. Tener configurado el archivo `.env` en la raíz del proyecto (basado en `.env.example`).
2. Docker y Docker Compose instalados.
3. **(Opcional)** El dominio por defecto `fed.local` debe apuntar a tu IP local en el archivo `/etc/hosts`.

---

## Orden de Ejecución (Paso a Paso)

Para un despliegue exitoso, se debe seguir este orden estrictamente:

### Paso 1: Generar la configuración base

> [!IMPORTANT]
Antes de levantar los contenedores, Synapse necesita generar sus archivos de configuración y llaves de firmado.

```bash
./generate_config.sh
```

*Esto creará la carpeta `data/` con el archivo `homeserver.yaml`.*

### Paso 2: Levantar la infraestructura

Levanta todos los servicios definidos en el Compose.

```bash
docker compose up -d
```

*Espera a que `chatsender_synapse` y `chatsender_db` aparezcan como `(healthy)` antes de continuar.*

### Paso 3: Registrar el usuario Administrador

Necesitas un usuario con privilegios de administrador para que el Backend pueda gestionar la creación y borrado de usuarios efímeros.

```bash
./register_admin.sh
```

> *Sigue los prompts para asignar un nombre de usuario (ej: `admin`) y una contraseña fuerte.*

### Paso 4: Obtener el Token de Acceso (Admin Token)

El Backend necesita el `SYNAPSE_ADMIN_TOKEN` para comunicarse con la API de Matrix. Este script realiza el login y extrae el token.

```bash
./synapse_admin_setup.sh
```

> [!IMPORTANT]
Copia el token resultante y pégalo en tu archivo `.env` en la variable `SYNAPSE_ADMIN_TOKEN`.

---

## Diccionario de Scripts

| Script | Función | Cuándo usarlo |
| --- | --- | --- |
| `generate_config.sh` | Crea el `homeserver.yaml` inicial. | Solo la primera vez (First run). |
| `register_admin.sh` | Registra un usuario admin en la DB. | Tras levantar los contenedores. |
| `synapse_admin_setup.sh` | Obtiene el Token vía API (HTTPS). | Siempre que el token expire o cambie. |
| `cleanup_users.py` *Deprecated*| Purga usuarios y mensajes expirados. | Automatizado (Cron) o manual para limpieza. |

---

## Notas de Seguridad y Nginx

Debido a la configuración de seguridad en el Proxy Inverso (Nginx):

1. **SSL/HTTPS**: Los scripts que atacan a la API (`synapse_admin_setup.sh`) deben usar el flag `-k` de `curl` si estás usando certificados autofirmados.
2. **Bloqueo de Navegador**: Nginx bloquea peticiones con header `text/html`. Los scripts de administración funcionan porque `curl` envía headers compatibles con API por defecto.
3. **Acceso Interno**: Si ejecutas los scripts desde fuera del contenedor, asegúrate de apuntar a `https://fed.local` y no a `localhost`, para que Nginx reconozca el `server_name`.

---

### ¿Qué sigue ahora?

Una vez que hayas pegado el `SYNAPSE_ADMIN_TOKEN` en tu `.env`, reinicia el backend para que cargue la nueva configuración:

```bash
docker compose restart backend
```
