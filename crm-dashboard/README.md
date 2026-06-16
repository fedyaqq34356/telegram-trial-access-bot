# Vio Agency CRM

CRM Dashboard для управления агентствами Halo Live: данные по девушкам, автоматическое
определение уровня и зоны риска, изменение процента, запуск Split, разграничение доступа
по агентствам. Тёмная тема, фиолетовые акценты, glassmorphism.

Стек: **FastAPI (Python)** + **Next.js (React/TypeScript)** + **PostgreSQL/SQLite**.
Интеграция с панелью `admin.livegirl.me` через `requests` + cookies (двухшаговый логин + 2FA).

---

## Структура

```
crm-dashboard/
  backend/          FastAPI: API, БД, парсер Halo, scheduler
    app/
      main.py       точка входа, seed суперадмина, старт планировщика
      models.py     SQLAlchemy модели
      routers/      auth, agencies, hosts, dashboard, risk, split, users, logs, settings, sync
      services/     halo_parser, sessions, sync_service, split_service, levels, scheduler, app_settings
    requirements.txt
    .env.example
  frontend/         Next.js (App Router) + Tailwind
    src/app/        страницы: login, dashboard, users, risk, agencies, split, admins, logs, settings
    src/components/ UI: Sidebar, StatsCard, бейджи, таблицы, модалки
    src/lib/        api-клиент, auth, agency-контекст, форматтеры
  deploy/           nginx.conf, systemd сервисы
  run-dev.sh        запуск dev-окружения одной командой
```

---

## Быстрый старт (разработка)

Требования: Python 3.11–3.12, Node.js 18+.

```bash
cd crm-dashboard
./run-dev.sh
```

Откройте <http://localhost:3000>. Логин по умолчанию: **admin / admin123**
(меняется в `backend/.env`, переменные `SUPERADMIN_USERNAME` / `SUPERADMIN_PASSWORD`).

Вручную:

```bash
# Backend
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # настройте секреты
uvicorn app.main:app --reload --port 8000

# Frontend (в другом терминале)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

> По умолчанию БД — SQLite (`backend/crm.db`), настройка не нужна.
> Для PostgreSQL задайте `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/crm` в `.env`.

---

## Как это работает

- **Авторизация CRM** — JWT (access 15 мин + refresh 7 дней), пароли — bcrypt.
- **Доступ по агентствам** — суперадмин видит всё; обычный админ — только разрешённые агентства.
  Права на агентство: просмотр / изменение % / запуск Split. Отдельный флаг — управление пользователями CRM.
- **Подключение к Halo Live** — при добавлении агентства вводятся логины/пароли (2 шага).
  Если включена 2FA — появится поле для кода Google Authenticator. Сессия (cookies) сохраняется в БД
  и переиспользуется; при истечении — повторный логин.
- **Автообновление** — scheduler каждые N минут (настройка) тянет данные всех агентств в кеш (`hosts`).
  Кнопка «Обновить данные» — принудительная синхронизация.
- **Уровни** считаются по заработку за 30 дней; **риск** — по коэффициенту за 30 дней против лимита уровня
  (безопасно / предупреждение при ≥90% лимита / в зоне риска при превышении). Лимиты настраиваются.
- **Split** — последовательная обработка девушек с балансом ≥ 100 coins (порог настраивается),
  пропуск при низком балансе и высоком коэффициенте дизлайков. История сохраняется.
- **Заработок** показывается в coins и USD (20 coins = 1 USD, настраивается).

---

## Деплой на VDS (Ubuntu 22.04+)

```bash
# 1. Зависимости системы
sudo apt update && sudo apt install -y python3-venv python3-pip nginx postgresql nodejs npm certbot python3-certbot-nginx

# 2. Код
sudo mkdir -p /opt/crm-dashboard && sudo chown -R $USER /opt/crm-dashboard
cp -r crm-dashboard/* /opt/crm-dashboard/

# 3. PostgreSQL
sudo -u postgres psql -c "CREATE USER crm WITH PASSWORD 'strong_password';"
sudo -u postgres psql -c "CREATE DATABASE crm OWNER crm;"

# 4. Backend
cd /opt/crm-dashboard/backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
#   в .env: DATABASE_URL=postgresql+psycopg2://crm:strong_password@localhost:5432/crm
#           JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
#           CORS_ORIGINS=https://crm.example.com
#           SUPERADMIN_PASSWORD=<надёжный пароль>

# 5. Frontend
cd /opt/crm-dashboard/frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=https://crm.example.com
npm run build

# 6. systemd
sudo cp /opt/crm-dashboard/deploy/crm-backend.service /etc/systemd/system/
sudo cp /opt/crm-dashboard/deploy/crm-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now crm-backend crm-frontend

# 7. nginx + SSL
sudo cp /opt/crm-dashboard/deploy/nginx.conf /etc/nginx/sites-available/crm
sudo ln -s /etc/nginx/sites-available/crm /etc/nginx/sites-enabled/
#   замените crm.example.com на ваш домен
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d crm.example.com
```

После деплоя: войдите под суперадмином → **Агентства** → добавьте агентства с кредами →
при необходимости введите код 2FA → создайте CRM-пользователей в разделе **Администраторы**.

---

## API (кратко)

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/auth/login` | вход, выдаёт JWT |
| GET | `/api/auth/me` | текущий пользователь + доступные агентства |
| GET | `/api/agencies` | список агентств (с учётом доступа) |
| POST/PUT/DELETE | `/api/agencies/...` | управление агентствами (суперадмин) |
| POST | `/api/agencies/{id}/login`, `/api/agencies/verify-2fa` | вход в Halo, 2FA |
| GET | `/api/hosts` | таблица девушек (поиск/фильтры/сортировка/пагинация) |
| POST | `/api/hosts/{id}/ratio` | изменить процент |
| GET | `/api/risk` | зона риска |
| GET | `/api/dashboard/stats` | карточки и статистика |
| POST | `/api/split/run`, GET `/api/split/history` | Split |
| GET/POST/PUT/DELETE | `/api/users` | CRM-пользователи |
| GET | `/api/logs/actions`, `/api/logs/security` | журналы |
| GET/PUT | `/api/settings` | настройки (курс, лимиты, интервал) |
| POST | `/api/sync` | принудительная синхронизация |

Документация Swagger — `http://localhost:8000/docs`.

---

## Безопасность

JWT, bcrypt, CORS только для своего домена, HTTPS (certbot), логирование действий
(`action_log`) и входов (`security_logs`), ограничение процента (макс. 20%),
разграничение доступа по агентствам на уровне API.
