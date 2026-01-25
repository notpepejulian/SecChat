# Workflow - Flujo de Trabajo con Git

## Estrategia de Ramas

Este proyecto utiliza **Git Flow** simplificado con dos ramas principales:

### 📋 Ramas Principales

#### `develop` (Desarrollo)
- Rama activa para desarrollo
- Contiene las últimas características en desarrollo
- Configuración: `docker-compose.dev.yml`
- Dockerfiles: `Dockerfile.dev` (backend y frontend)
- Características:
  - Hot reload activado
  - Volúmenes montados para desarrollo
  - Backend ejecuta como root para evitar problemas con SELinux
  - Frontend con HMR (Hot Module Replacement)

#### `main` (Producción)
- Rama estable para producción
- Solo contiene código testeado y listo para desplegar
- Configuración: `docker-compose.prod.yml`
- Dockerfiles: `Dockerfile.prod` (backend y frontend)
- Características:
  - Sin hot reload
  - Sin volúmenes de código montados
  - Backend ejecuta con usuario no privilegiado
  - Frontend compilado estáticamente

## 🔄 Flujo de Trabajo

### 1. Desarrollo de nuevas características

```bash
# Asegurarse de estar en develop
git checkout develop
git pull origin develop

# Crear rama para nueva característica
git checkout -b feature/nombre-caracteristica

# Desarrollar y hacer commits
git add .
git commit -m "feat: descripción de la característica"

# Subir rama
git push origin feature/nombre-caracteristica

# Crear Pull Request hacia develop
```

### 2. Corrección de bugs

```bash
# Crear rama desde develop
git checkout develop
git checkout -b fix/descripcion-bug

# Corregir y hacer commits
git add .
git commit -m "fix: descripción de la corrección"

# Subir y crear PR hacia develop
git push origin fix/descripcion-bug
```

### 3. Release a producción

```bash
# Cuando develop esté estable y listo
git checkout main
git pull origin main

# Merge desde develop
git merge develop

# Tag de versión
git tag -a v1.0.0 -m "Release v1.0.0"

# Subir cambios y tags
git push origin main
git push origin --tags
```

### 4. Hotfix en producción

```bash
# Crear rama desde main para urgencias
git checkout main
git checkout -b hotfix/descripcion

# Corregir
git add .
git commit -m "hotfix: descripción"

# Merge a main
git checkout main
git merge hotfix/descripcion

# Merge también a develop
git checkout develop
git merge hotfix/descripcion

# Subir cambios
git push origin main
git push origin develop
```

## 🚀 Despliegue

### Desarrollo (rama develop)
```bash
# Usar docker-compose.dev.yml
./deploy.sh dev
# O con make
make dev
# O directamente con docker-compose (symlink apunta a .dev.yml)
docker-compose up -d
```

### Producción (rama main)
```bash
# Usar docker-compose.prod.yml
./deploy.sh prod
# O con make
make prod
# O directamente
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 Convenciones de Commits

Seguimos **Conventional Commits**:

- `feat:` - Nueva característica
- `fix:` - Corrección de bug
- `docs:` - Cambios en documentación
- `style:` - Formato, sin cambios de código
- `refactor:` - Refactorización de código
- `perf:` - Mejoras de rendimiento
- `test:` - Añadir o corregir tests
- `chore:` - Tareas de mantenimiento
- `ci:` - Cambios en CI/CD

Ejemplos:
```bash
git commit -m "feat: añadir autenticación JWT al backend"
git commit -m "fix: corregir error de conexión a MariaDB"
git commit -m "docs: actualizar README con nuevas instrucciones"
```

## 🔍 Antes de hacer merge a main

Checklist:
- [ ] Todos los tests pasan
- [ ] El código está documentado
- [ ] No hay secretos o credenciales hardcodeadas
- [ ] Las variables de entorno están documentadas
- [ ] El README está actualizado
- [ ] Los logs no muestran errores
- [ ] Los healthchecks funcionan correctamente

## 🌿 Estado Actual

```
main (producción)
  └── docker-compose.prod.yml
  └── Dockerfile.prod (backend y frontend)
  └── Sin volúmenes de código
  └── Usuario no privilegiado

develop (desarrollo) ← RAMA ACTUAL
  └── docker-compose.dev.yml
  └── docker-compose.yml (symlink → docker-compose.dev.yml)
  └── Dockerfile.dev (backend y frontend)
  └── Volúmenes montados
  └── Hot reload activado
```

## 🛠️ Comandos Útiles

Ver rama actual:
```bash
git branch
```

Ver diferencias entre ramas:
```bash
git diff develop..main
```

Ver commits pendientes de merge:
```bash
git log main..develop --oneline
```

Cambiar de rama:
```bash
# A desarrollo
git checkout develop

# A producción
git checkout main
```

## 📦 Archivos específicos por rama

### Solo en `develop`:
- Configuración de desarrollo con hot reload
- Volúmenes montados para edición en vivo

### Solo en `main`:
- Configuración optimizada para producción
- Build estáticos
- Configuración de SSL/TLS (cuando se implemente)

### En ambas:
- README.md
- .env.example
- Código fuente
- Dockerfiles (ambos: dev y prod)
