# Sentiment Analysis ML Service

Учебный проект. В этой ветке — структура и docker-compose для локального запуска сервисов:
- app (FastAPI / Python)
- web-proxy (nginx)
- rabbitmq (message broker)
- database (Postgres)

Файлы:
- docker-compose.yml — конфигурация для разработки
- Dockerfile.app — сборка образа приложения
- .env.template — шаблон переменных окружения