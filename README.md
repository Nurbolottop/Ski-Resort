# Django Project Skeleton

Готовый скелет для быстрого старта Django-проектов: от сайтов-визиток до админок и CRM. Копируешь папку, меняешь одну переменную — получаешь работающий изолированный стек.

**Стек:** Django 5.2 · PostgreSQL 14 · Redis 6 · Gunicorn · Docker Compose

---

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Переменные окружения](#переменные-окружения)
- [Как работает нейминг](#как-работает-нейминг)
- [Несколько проектов на одном сервере](#несколько-проектов-на-одном-сервере)
- [Структура проекта](#структура-проекта)
- [Разработка](#разработка)
- [Настройки Django](#настройки-django)
- [Деплой](#деплой)
- [Telegram bot](#telegram-bot-опционально)
- [Типовые проблемы](#типовые-проблемы)
- [Что стоит доделать под свой проект](#что-стоит-доделать-под-свой-проект)

---

## Быстрый старт

```bash
./scripts/init-project.sh myproject
```

Скрипт создаст `.env`: подберёт свободные порты, сгенерирует уникальные `SECRET_KEY` и пароль БД, проверит, что имя проекта ещё не занято на этом сервере. Останется вписать свой домен в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.

Вручную — тоже можно:

```bash
cp .envtest .env
```

В `.envtest` каждая переменная помечена: `[МЕНЯТЬ]`, `[УНИКАЛЬНОЕ]` (не должно совпадать с другими проектами на сервере) или `[НЕ ТРОГАТЬ]`.

Поднимаешь:

```bash
docker compose up --build
```

Открываешь `http://127.0.0.1:8084`, админка — `/admin/`.

Создать суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Переменные окружения

Все переменные живут в `.env` в корне. Шаблон — `.envtest` (он в репозитории, `.env` — нет).

### Обязательно менять на новом проекте

| Переменная | Что это |
|---|---|
| `COMPOSE_PROJECT_NAME` | Имя проекта. Префикс для всех контейнеров, volume и сети |
| `SECRET_KEY` | Ключ Django. На каждом проекте — свой |
| `ALLOWED_HOSTS` | Домены через запятую: `example.com,127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | Origin'ы **со схемой**: `https://example.com` |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Доступы к базе |

### Порты на хосте

| Переменная | По умолчанию | Куда ведёт |
|---|---|---|
| `WEB_PORT` | `8084` | Django (внутри контейнера всегда `8000`) |
| `DB_PORT` | `5433` | Postgres (внутри `5432`) |
| `REDIS_PORT` | `6389` | Redis (внутри `6379`) |

Задаются отдельно под каждый проект, чтобы не конфликтовать с уже занятыми портами на сервере. Внутренние порты контейнеров не меняются никогда.

### Менять не нужно

| Переменная | Значение | Почему |
|---|---|---|
| `POSTGRES_HOST` | `db` | Имя сервиса в compose — по нему контейнеры находят друг друга |
| `POSTGRES_PORT` | `5432` | Внутренний порт Postgres |
| `REDIS_URL` | `redis://redis:6379/0` | То же самое для Redis |

### Прочее

`LANGUAGE_CODE` (`ru`), `TIME_ZONE` (`Asia/Bishkek`) — читаются в `base.py` с этими значениями по умолчанию.

---

## Как работает нейминг

Меняешь одну строку — переименовывается весь стек. Docker Compose подставляет `COMPOSE_PROJECT_NAME` как префикс:

| Объект в compose | Реальное имя при `COMPOSE_PROJECT_NAME=myproject` |
|---|---|
| сервис `db` | контейнер `myproject-db-1` |
| сервис `redis` | контейнер `myproject-redis-1` |
| сервис `web` | контейнер `myproject-web-1` |
| volume `postgres_data` | `myproject_postgres_data` |
| сеть по умолчанию | `myproject_default` |

Благодаря этому на одном сервере спокойно живут несколько проектов из этого скелета — ничего не пересекается.

> **Почему не `db_${PROJECT_NAME}`.** Docker Compose интерполирует переменные только в *значениях* YAML, но не в *ключах*. Имя сервиса и имя volume — это ключи, и такой файл не проходит даже валидацию:
> ```
> validating docker-compose.yml: volumes additional properties 'postgres_data_${PROJECT_NAME}' not allowed
> ```
> `COMPOSE_PROJECT_NAME` решает ту же задачу штатным способом. Поэтому же в compose нет `container_name` — он мешает Compose самому давать уникальные имена.

Проверить, что подставилось:

```bash
docker compose config | head -20
```

---

## Несколько проектов на одном сервере

Скелет рассчитан на то, что на одной машине крутится несколько проектов с одинаковой структурой. Что изолируется само, а что нужно задать:

| Ресурс | Изоляция | Комментарий |
|---|---|---|
| Контейнеры | ✅ автоматически | `clinic-web-1` vs `shop-web-1` |
| Volume с данными | ✅ автоматически | `clinic_postgres_data` vs `shop_postgres_data` |
| Сеть | ✅ автоматически | `clinic_default` vs `shop_default` |
| Docker-образы | ✅ автоматически | `clinic-web` vs `shop-web` |
| Данные Postgres | ✅ автоматически | у каждого проекта свой контейнер БД и свой volume |
| **Порты на хосте** | ⚠️ задаются вручную | `WEB_PORT` / `DB_PORT` / `REDIS_PORT` |
| **`SECRET_KEY`, пароль БД** | ⚠️ задаются вручную | при `cp .envtest .env` скопируются одинаковыми |

Первые пять строк обеспечивает `COMPOSE_PROJECT_NAME` — достаточно, чтобы имя было уникальным. Две последние — единственное, где можно ошибиться, и ровно их закрывает `init-project.sh`.

**Важно про порты:** занятость определяется не только запущенными контейнерами. Остановленный проект сокет не держит, но его порты всё равно заняты — он их вернёт при следующем старте. Поэтому скрипт смотрит ещё и в `.env` соседних проектов, лежащих рядом в том же каталоге (`/srv/clinic`, `/srv/shop`, …).

Пример последовательной инициализации трёх проектов рядом:

```
/srv/clinic  →  web 8080, db 5435, redis 6380
/srv/shop    →  web 8081, db 5436, redis 6381
/srv/blog    →  web 8082, db 5437, redis 6382
```

Диапазоны поиска: web `8080–8199`, postgres `5433–5499`, redis `6380–6499`.

Если проекты лежат в **разных** каталогах, скрипт соседей не увидит — тогда проверь порты сам:

```bash
docker ps -a --format 'table {{.Label "com.docker.compose.project"}}\t{{.Ports}}'
```

Занять одно имя проекта дважды скрипт тоже не даст — он проверяет существующие volume и контейнеры и откажется работать. Это важнее портов: конфликт порта виден сразу по ошибке запуска, а вот два проекта с одним `COMPOSE_PROJECT_NAME` молча начнут делить один volume с данными.

В проде наружу публикуется только web-порт, и то на `127.0.0.1`. Postgres и Redis портов на хост не пробрасывают вообще — они доступны лишь внутри сети своего проекта, поэтому пересечься между проектами не могут.

---

## Структура проекта

```
.
├── app/                       # Django-проект
│   ├── core/                  # Конфигурация
│   │   ├── settings/
│   │   │   ├── base.py        # Общие настройки
│   │   │   ├── dev.py         # DEBUG=True
│   │   │   └── prod.py        # DEBUG=False, security, logging
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/                  # Бизнес-приложения
│   │   ├── base/              # Заготовка под общий код
│   │   ├── cms/               # Заготовка под контент
│   │   └── contacts/          # Заготовка под контакты/заявки
│   ├── templates/
│   │   └── include/           # header / footer / homepage
│   ├── static/                # Исходная статика
│   └── manage.py
├── docker/
│   └── Dockerfile
├── scripts/
│   ├── entrypoint.sh          # Ожидание БД → migrate → collectstatic
│   └── init-project.sh        # Генерация .env под новый проект
├── docker-compose.yml         # dev
├── docker-compose.prod.yml    # prod
├── .envtest                   # Шаблон переменных
└── requirements.txt
```

Compose-файлы лежат **в корне рядом с `.env`** намеренно: Compose читает `.env` из директории compose-файла, и если унести их в `docker/`, переменные молча перестанут подхватываться.

Приложения лежат в пакете `apps/`, поэтому в `INSTALLED_APPS` они прописаны как `apps.base`, а в `apps.py` указано `name = 'apps.base'`.

---

## Разработка

### Основные команды

```bash
docker compose up --build          # поднять стек
docker compose up -d               # в фоне
docker compose down                # остановить
docker compose logs -f web         # логи Django
docker compose restart web         # перезапустить
```

Код примонтирован в контейнер (`./app:/app`), поэтому dev server сам перезагружается при правках — пересобирать образ нужно только при изменении `requirements.txt`.

### manage.py

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell
docker compose exec web python manage.py test
```

**Миграции создаются локально и коммитятся в репозиторий.** На сервере `entrypoint.sh` выполняет только `migrate` — `makemigrations` там намеренно нет, иначе схема на проде начнёт расходиться с кодом.

### Добавить новое приложение

```bash
docker compose exec web mkdir -p apps/myapp
docker compose exec web python manage.py startapp myapp apps/myapp
```

`startapp` с указанием директории требует, чтобы она уже существовала — отсюда `mkdir`.

Дальше три шага:

1. В `apps/myapp/apps.py` поправить путь:
   ```python
   class MyappConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'apps.myapp'
   ```

2. В `core/settings/base.py` добавить в `INSTALLED_APPS`:
   ```python
   'apps.myapp',
   ```

3. В `core/urls.py` подключить маршруты:
   ```python
   path('myapp/', include('apps.myapp.urls')),
   ```

### База данных

Подключиться извне (например, из DBeaver): хост `127.0.0.1`, порт из `DB_PORT`, остальное из `.env`.

```bash
# консоль psql (подставь значения из .env)
docker compose exec db psql -U namex_user -d namex

# дамп базы на хост
docker compose exec db pg_dump -U namex_user -d namex > backup.sql

# восстановление из дампа
docker compose exec -T db psql -U namex_user -d namex < backup.sql
```

Переменные здесь раскрывает хостовый шелл, а не контейнер, поэтому `$POSTGRES_USER` подставится пустым — пиши значения явно.

Полный сброс базы (**удаляет все данные**):

```bash
docker compose down -v
```

---

## Настройки Django

Настройки разделены на три файла. `dev.py` и `prod.py` импортируют всё из `base.py` и переопределяют нужное.

Выбор файла — через переменную `DJANGO_SETTINGS_MODULE`, она задана в compose:

- dev → `core.settings.dev`
- prod → `core.settings.prod`

По умолчанию (в `manage.py`, `wsgi.py`, `asgi.py`) используется `core.settings.dev`.

### base.py

`SECRET_KEY` читается из окружения, и при его отсутствии проект падает на старте — так не получится случайно уехать в прод с дефолтным ключом. `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` парсятся из строк через запятую.

Пути: `STATICFILES_DIRS = [app/static]`, `STATIC_ROOT = app/staticfiles` (туда пишет `collectstatic`), `MEDIA_ROOT = app/media`.

### dev.py

`DEBUG = True`, secure-cookies выключены (иначе по http не залогиниться в админку).

### prod.py

- `DEBUG = False`, `SESSION_COOKIE_SECURE` и `CSRF_COOKIE_SECURE` включены
- `SECURE_PROXY_SSL_HEADER` + `USE_X_FORWARDED_HOST` — Django работает за nginx, который терминирует HTTPS. Без этого он считает запрос http-запросом и ломает CSRF и редиректы
- `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS = 'DENY'`
- `LOGGING` в stdout — при `DEBUG=False` ошибки иначе никуда не пишутся, а так они видны в `docker compose logs`
- HSTS закомментирован намеренно: включай только когда HTTPS точно работает, иначе браузеры запомнят домен и http перестанет открываться

---

## Деплой

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Отличия от dev:

| | dev | prod |
|---|---|---|
| Сервер | runserver | gunicorn, 3 воркера, timeout 120 |
| Настройки | `core.settings.dev` | `core.settings.prod` |
| Рестарт | нет | `restart: always` |
| Порт Django | `127.0.0.1:8084` | `127.0.0.1:8000` |
| Порты БД/Redis | проброшены наружу | закрыты |

`restart: always` означает, что стек сам поднимется после перезагрузки сервера. Порт публикуется только на `127.0.0.1` — снаружи приложение доступно исключительно через nginx.

### nginx на хосте

```nginx
server {
    listen 80;
    server_name example.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/project/app/staticfiles/;
    }

    location /media/ {
        alias /path/to/project/app/media/;
    }
}
```

`X-Forwarded-Proto` обязателен — на него опирается `SECURE_PROXY_SSL_HEADER` в `prod.py`.

HTTPS: `certbot --nginx -d example.com`.

### Обновление на сервере

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f web
```

Миграции и `collectstatic` выполнит `entrypoint.sh` при старте контейнера.

---

## Telegram bot (опционально)

Сервис `bot` вынесен в Compose-профиль и **по умолчанию не запускается** — он ждёт management-команду `manage.py bot`, которой в скелете пока нет. Без профиля он не поднимается и не мешает стеку.

Когда напишешь команду (`apps/<app>/management/commands/bot.py`):

```bash
docker compose --profile bot up -d                              # dev
docker compose -f docker-compose.prod.yml --profile bot up -d   # prod
```

Бот использует тот же образ и те же переменные окружения, что и `web`. В `requirements.txt` уже есть `pyTelegramBotAPI`.

---

## Типовые проблемы

**`port is already allocated`** — порт занят другим проектом. Поменяй `WEB_PORT` / `DB_PORT` / `REDIS_PORT` в `.env`. Посмотреть, кто занял: `lsof -i :8084`.

**`The "COMPOSE_PROJECT_NAME" variable is not set`** — команда запущена не из корня. Compose ищет `.env` рядом с compose-файлом; запускай из директории проекта или добавляй `--env-file .env`.

**`could not translate host name "db"`** — в `.env` изменили `POSTGRES_HOST`. Должно быть ровно `db` — это имя сервиса.

**`SECRET_KEY не задан в переменных окружения`** — нет `.env` или в нём нет `SECRET_KEY`. Сделай `cp .envtest .env`.

**CSRF-ошибки на проде** — проверь `CSRF_TRUSTED_ORIGINS` (должны быть со схемой `https://`) и что nginx передаёт `X-Forwarded-Proto`.

**Статика не отдаётся на проде** — при `DEBUG=False` Django её не раздаёт, это задача nginx. Проверь `alias` на `app/staticfiles/` и что `collectstatic` отработал (видно в логах `web`).

**Изменения в коде не применяются** — если правил `requirements.txt` или `Dockerfile`, нужна пересборка: `docker compose up -d --build`.

---

## Что стоит доделать под свой проект

Скелет намеренно оставлен минимальным. Что в нём отсутствует и о чём стоит подумать на старте:

- **Кастомная модель пользователя.** `AUTH_USER_MODEL` не задан. Завести `apps/users` с `class User(AbstractUser)` нужно **до первой миграции** — потом заменить модель практически невозможно. Самый дорогой пункт из списка.
- **DRF.** Если проект на API — в `requirements.txt` нет `djangorestframework`, `django-cors-headers`, `drf-spectacular`, `django-filter`. Плюс понадобится блок `REST_FRAMEWORK` в `base.py`.
- **Абстрактные модели в `apps/base`.** Приложение пустое, а напрашиваются `TimeStampedModel` (created_at / updated_at), `SEOModel`, общие менеджеры.
- **Redis.** Контейнер поднимается и `REDIS_URL` есть в `.env`, но `CACHES` в настройках не сконфигурирован — сейчас Redis работает вхолостую.
- **`django-ckeditor`.** Django выдаёт предупреждение при каждом старте: пакет несёт CKEditor 4.22.1 с неисправленными уязвимостями. Стоит перейти на `django-ckeditor-5` или TinyMCE.
- **Приложения `cms` и `contacts`** — пустые заготовки. Удали ненужные (из `INSTALLED_APPS` и `core/urls.py` тоже) или наполни.
- **Тесты и CI.** Есть только пустые `tests.py` от `startapp`.
