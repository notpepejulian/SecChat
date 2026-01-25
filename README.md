# ChatSender - Servidor de Mensajería Local

Servidor de mensajería privado basado en Matrix Synapse con interfaz web Astro, backend FastAPI y base de datos MariaDB, todo orquestado con Docker Compose.

## 🏗️ Arquitectura

```
┌─────────────┐
│   Nginx     │  Puerto 80 (Proxy Inverso)
│   (Alpine)  │
└──────┬──────┘
       │
       ├───────────────────┬────────────────────┬─────────────────┐
       │                   │                    │                 │
┌──────▼──────┐    ┌───────▼────────┐   ┌──────▼──────┐  ┌──────▼──────┐
│  Frontend   │    │    Backend     │   │   Synapse   │  │   MariaDB   │
│   (Astro)   │    │   (FastAPI)    │   │   (Matrix)  │  │     (DB)    │
│  Puerto 4321│    │   Puerto 8000  │   │ Puerto 8008 │  │ Puerto 3306 │
└─────────────┘    └────────────────┘   └─────────────┘  └─────────────┘
```

## 📋 Requisitos Previos

- Docker >= 24.0
- Docker Compose >= 2.20
- Sistema operativo con soporte SELinux (Fedora, RHEL, CentOS) o sin él

##  Inicio Rápido

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd ChatSender
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales seguras
nano .env
```

### 3. Inicializar Synapse (primera vez)

```bash
cd synapse
./init-synapse.sh
```

Luego configura el archivo `homeserver.yaml` para usar MariaDB:

```bash
docker run --rm -it -v chatsender_synapse_data:/data alpine sh
# Dentro del contenedor:
cd /data
vi homeserver.yaml
```

Busca la sección `database:` y reemplázala con:

```yaml
database:
  name: psycopg2
  args:
    user: synapse_user
    password: <tu_DB_PASSWORD_del_.env>
    database: synapse
    host: db
    port: 3306
    cp_min: 5
    cp_max: 10
```

### 4. Levantar los servicios

```bash
# Desarrollo (por defecto)
docker-compose up -d
# O explícitamente
docker-compose -f docker-compose.dev.yml up -d

# Producción
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Verificar el estado

```bash
docker-compose ps
docker-compose logs -f
```

## 🔧 Servicios

### MariaDB (Base de Datos)
- **Puerto interno**: 3306
- **Usuario**: `synapse_user`
- **Base de datos**: `synapse`
- **Healthcheck**: Verifica conexión cada 10s

### Synapse (Matrix Server)
- **Puerto interno**: 8008
- **Servidor**: `fed.local`
- **Endpoints**: `/_matrix/*`, `/_synapse/*`
- **Healthcheck**: `/health` cada 30s

### Backend (FastAPI)
- **Puerto interno**: 8000
- **Endpoints**: `/api/*`
- **Características**:
  - Hot reload en desarrollo
  - Conexión a MariaDB vía SQLAlchemy
  - Cliente HTTP para comunicación con Synapse
  - Healthcheck: `/health`

### Frontend (Astro)
- **Puerto interno**: 4321
- **Modo**: Desarrollo con HMR
- **Hot Module Replacement**: Soportado vía WebSocket

### Nginx (Proxy Inverso)
- **Puerto externo**: 80
- **Rutas**:
  - `/` → Frontend
  - `/api/*` → Backend
  - `/_matrix/*` → Synapse
  - `/_synapse/*` → Synapse (Admin API)
  - `/.well-known/matrix/*` → Autodescubrimiento Matrix

##  Comandos Útiles

### Ver logs de todos los servicios
```bash
# Desarrollo
docker-compose logs -f
# Producción
docker-compose -f docker-compose.prod.yml logs -f
```

### Ver logs de un servicio específico
```bash
docker-compose logs -f backend
docker-compose logs -f synapse
```

### Reiniciar un servicio
```bash
docker-compose restart backend
```

### Reconstruir imágenes
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Detener todos los servicios
```bash
docker-compose down
```

### Detener y eliminar volúmenes
```bash
docker-compose down -v
```

### Acceder al shell de un contenedor
```bash
docker-compose exec backend bash
docker-compose exec db mariadb -u synapse_user -p
```

### Probar endpoints

```bash
# Backend health
curl http://localhost/api/health

# Verificar conexión DB
curl http://localhost/api/db-status

# Verificar conexión Synapse
curl http://localhost/api/synapse-version

# Synapse versions endpoint
curl http://localhost/_matrix/client/versions
```

##  Estructura del Proyecto

```
ChatSender/
├── backend/
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   └── package.json
├── nginx/
│   └── conf.d/
│       └── nginx.conf
├── synapse/
│   └── init-synapse.sh
├── mariadb/
├── vpn/
├── docker-compose.yml -> docker-compose.dev.yml (symlink)
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── deploy.sh
├── Makefile
├── .env
└── .env.example
```

## 🔒 Seguridad

### SELinux
El proyecto está configurado para funcionar con SELinux usando:
- Volúmenes con flag `:Z` para contexto privado
- Volúmenes con flag `:z` para contexto compartido

### Desarrollo vs Producción

**Desarrollo (actual)**:
- Backend ejecuta como root para compatibilidad con volúmenes montados
- Frontend en modo desarrollo con HMR
- No hay SSL/TLS (solo HTTP)

**Producción (recomendado)**:
1. Cambiar Dockerfile del backend para usar usuario no privilegiado
2. Usar `Dockerfile.prod` para el frontend
3. Configurar Nginx con SSL/TLS (Let's Encrypt)
4. No montar volúmenes de código fuente
5. Usar secrets de Docker para credenciales
6. Activar VPN (WireGuard)

##  VPN (WireGuard)

La configuración de WireGuard está comentada en `docker-compose.yml`. Para activarla:

1. Descomentar la sección `vpn` en el archivo
2. Configurar la variable `VPN_SERVER_IP` en `.env`
3. Ajustar permisos y módulos del kernel:

```bash
sudo modprobe wireguard
```

4. Levantar el servicio:

```bash
docker-compose up -d vpn
```

5. Los archivos de configuración de peers estarán en `./vpn/config/`

## 🐛 Troubleshooting

### Error: "Permission denied" en volúmenes
- **Causa**: SELinux bloqueando acceso
- **Solución**: Verificar que los volúmenes usan `:Z` o `:z`

### Synapse no inicia
- **Causa**: Falta configuración inicial o DB no conectada
- **Solución**: Ejecutar `./synapse/init-synapse.sh` y configurar homeserver.yaml

### Backend no conecta a MariaDB
- **Causa**: Variables de entorno incorrectas o DB no healthy
- **Solución**: Verificar `.env` y esperar a que MariaDB esté healthy

### Frontend no accesible
- **Causa**: No está en la red `internal`
- **Solución**: Verificar que docker-compose.yml incluye `networks: - internal`

### Nginx 502 Bad Gateway
- **Causa**: Servicios backend no están listos
- **Solución**: Esperar a que todos los healthchecks estén OK

```bash
docker-compose ps
```

## 📊 Monitoreo

### Estado de healthchecks
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Uso de recursos
```bash
docker stats
```

### Logs en tiempo real
```bash
docker-compose logs -f --tail=100
```

## 🚧 Próximas Mejoras

- [ ] Implementar autenticación JWT en el backend
- [ ] Añadir rate limiting en Nginx
- [ ] Configurar backups automáticos de MariaDB
- [ ] Implementar monitoreo con Prometheus + Grafana
- [ ] Añadir soporte para SSL/TLS
- [ ] Documentar API del backend con Swagger/OpenAPI
- [ ] Implementar tests automatizados
- [ ] CI/CD con GitHub Actions

## 📝 Licencia

[Tu licencia aquí]

## 👥 Contribución

[Instrucciones de contribución aquí]
