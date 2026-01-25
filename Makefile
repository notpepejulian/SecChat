.PHONY: help build up down restart logs ps clean dev prod init-synapse health

# Variables
COMPOSE_FILE=docker-compose.dev.yml
COMPOSE_FILE_PROD=docker-compose.prod.yml

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Levantar entorno de desarrollo
	@./deploy.sh dev

prod: ## Levantar entorno de producción
	@./deploy.sh prod

build: ## Construir imágenes de Docker
	docker-compose -f $(COMPOSE_FILE) build

build-prod: ## Construir imágenes para producción
	docker-compose -f $(COMPOSE_FILE_PROD) build

up: ## Levantar servicios en modo desarrollo
	docker-compose -f $(COMPOSE_FILE) up -d

up-prod: ## Levantar servicios en modo producción
	docker-compose -f $(COMPOSE_FILE_PROD) up -d

down: ## Detener servicios
	docker-compose -f $(COMPOSE_FILE) down

down-all: ## Detener servicios y eliminar volúmenes
	docker-compose -f $(COMPOSE_FILE) down -v

restart: ## Reiniciar servicios
	docker-compose -f $(COMPOSE_FILE) restart

logs: ## Ver logs de todos los servicios
	docker-compose -f $(COMPOSE_FILE) logs -f --tail=100

logs-backend: ## Ver logs del backend
	docker-compose -f $(COMPOSE_FILE) logs -f backend

logs-frontend: ## Ver logs del frontend
	docker-compose -f $(COMPOSE_FILE) logs -f frontend

logs-synapse: ## Ver logs de Synapse
	docker-compose -f $(COMPOSE_FILE) logs -f synapse

logs-nginx: ## Ver logs de Nginx
	docker-compose -f $(COMPOSE_FILE) logs -f nginx

logs-db: ## Ver logs de MariaDB
	docker-compose -f $(COMPOSE_FILE) logs -f db

ps: ## Ver estado de los servicios
	docker-compose -f $(COMPOSE_FILE) ps

health: ## Verificar salud de los servicios
	@echo "=== Estado de los servicios ==="
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep chatsender || echo "No hay servicios corriendo"
	@echo ""
	@echo "=== Healthchecks ==="
	@echo -n "MariaDB: "
	@docker exec chatsender_db mariadb-admin ping -h localhost --silent && echo "✅ OK" || echo "❌ FAIL"
	@echo -n "Backend: "
	@curl -s http://localhost/api/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"
	@echo -n "Synapse: "
	@curl -s http://localhost/_matrix/client/versions > /dev/null && echo "✅ OK" || echo "❌ FAIL"
	@echo -n "Frontend: "
	@curl -s http://localhost/ > /dev/null && echo "✅ OK" || echo "❌ FAIL"

shell-backend: ## Acceder al shell del backend
	docker-compose -f $(COMPOSE_FILE) exec backend bash

shell-db: ## Acceder al shell de MariaDB
	docker-compose -f $(COMPOSE_FILE) exec db mariadb -u synapse_user -p

shell-synapse: ## Acceder al shell de Synapse
	docker-compose -f $(COMPOSE_FILE) exec synapse bash

shell-nginx: ## Acceder al shell de Nginx
	docker-compose -f $(COMPOSE_FILE) exec nginx sh

init-synapse: ## Inicializar configuración de Synapse
	@./synapse/init-synapse.sh

clean: ## Limpiar contenedores, imágenes y volúmenes huérfanos
	docker-compose -f $(COMPOSE_FILE) down
	docker system prune -f

clean-all: ## Limpiar TODO (contenedores, imágenes, volúmenes, caché)
	docker-compose -f $(COMPOSE_FILE) down -v
	docker system prune -af --volumes

rebuild: ## Reconstruir y reiniciar servicios
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	docker-compose -f $(COMPOSE_FILE) up -d

test-backend: ## Probar endpoints del backend
	@echo "=== Probando Backend ==="
	@echo "Health:"
	@curl -s http://localhost/api/health | jq '.' || echo "Error"
	@echo ""
	@echo "DB Status:"
	@curl -s http://localhost/api/db-status | jq '.' || echo "Error"
	@echo ""
	@echo "Synapse Version:"
	@curl -s http://localhost/api/synapse-version | jq '.' || echo "Error"

test-synapse: ## Probar endpoint de Synapse
	@echo "=== Probando Synapse ==="
	@curl -s http://localhost/_matrix/client/versions | jq '.' || echo "Error"

stats: ## Ver estadísticas de recursos
	docker stats --no-stream
