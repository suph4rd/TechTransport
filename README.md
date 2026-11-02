# Tech Transport

Локальный MVP поиска техники в Беларуси. Реализован этап 1 из `start_project_plan.md`: FastAPI, Vue 3 + TypeScript, PostgreSQL, Alembic и Docker Compose.

## Запуск

Нужны Docker Engine / Docker Desktop и Docker Compose v2. Из корня проекта:

```sh
cp .env.example .env
docker compose up --build -d
```

Первый запуск скачивает образы и зависимости. Backend ожидает готовность PostgreSQL и автоматически применяет миграции перед запуском. Frontend ожидает готовность backend.

- Приложение: http://localhost:5173
- OpenAPI: http://localhost:8000/docs
- Проверка процесса: http://localhost:8000/api/health/live
- Проверка подключения к БД: http://localhost:8000/api/health/ready

Frontend обращается к `/api` через Vite proxy: браузеру не требуется доступ к внутреннему имени `backend`. Порты доступны только локально. Настройки портов, БД и логирования находятся в `.env.example`; файл `.env` не включается в Git. Если пароль содержит специальные символы URL, его значение в `DATABASE_URL` необходимо кодировать; для локального Compose используйте пароль из букв, цифр, дефисов и подчёркиваний.

## Управление

```sh
docker compose ps
docker compose logs -f backend frontend db
docker compose restart
docker compose down
docker compose up -d
```

`restart` перезапускает существующие контейнеры. `down` удаляет контейнеры и сеть, сохраняя данные. После изменения зависимостей, кода или переменных окружения выполните `docker compose up --build -d`.

**`docker compose down -v` удаляет БД и фотографии без восстановления.** Не используйте эту команду для обычного перезапуска. Данные PostgreSQL и фотографии хранятся в отдельных именованных volumes `postgres_data` и `photos_data`. Изменение пароля в `.env` не меняет пароль уже инициализированной БД.

## Миграции

```sh
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1
```

Для создания миграции с сохранением файла в рабочем каталоге:

```sh
docker compose run --rm -v "$(pwd)/backend:/app" backend alembic revision --autogenerate -m "describe change"
```

Новые модели нужно импортировать в `migrations/env.py`, чтобы Alembic видел их metadata. Начальная миграция `0001` фиксирует основу; предметные таблицы появятся на следующих этапах. Сессия БД закрывается после запроса, при исключении откатывается; изменяющие операции должны явно вызывать `commit()`.

## Проверки

```sh
docker compose exec backend python -m pytest -q
docker compose exec frontend npm run build
```

Прямые зависимости закреплены в `backend/requirements*.txt` и `frontend/package.json`, транзитивные Python-зависимости закреплены в `backend/requirements.lock`, npm использует `package-lock.json`. Python 3.12 и Node 22 поставляются в контейнерах.

Ошибки API имеют формат `{"error":{"code":"...","message":"...","details":[]}}`. Ответ readiness возвращает 503 при недоступности БД. Тела запросов, query string, cookies, SQL-параметры и тексты внутренних исключений не журналируются. Access log Uvicorn выключен; локальная SMS-заглушка будет добавлена на этапе 2.

Это окружение локальной разработки: frontend работает через Vite dev server. Вход, справочник, карточки, фотографии и карта запланированы в этапах 2–7. Настоящие SMS и production-развёртывание пока не реализованы.

Известное ограничение проверок: Starlette сообщает о будущей замене httpx на httpx2 в тестовом клиенте; текущие тесты проходят. Визуальная проверка интерфейса в браузере пока не проводилась.
