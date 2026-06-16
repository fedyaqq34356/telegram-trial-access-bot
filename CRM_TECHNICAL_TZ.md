# Техническое ТЗ для разработки — CRM / Dashboard для Halo Live агентств

## Стек

- **Backend**: Python + FastAPI
- **Frontend**: Next.js (React)
- **БД**: PostgreSQL
- **Парсинг**: requests (сессии через cookies) — Playwright только для действий если API не сработает
- **Деплой**: VDS Ubuntu, nginx + systemd

---

## Архитектура

```
Browser (Next.js)
    ↓ REST API
FastAPI Backend
    ↓ PostgreSQL (хранение сессий, пользователей, истории)
    ↓ Halo Live API (через requests + cookies)
```

---

## Аутентификация в Halo Live

Панель: `https://admin.livegirl.me`
PHP/7.2.34 backend, nginx/1.8.1

### Двухшаговый логин

**Шаг 1** — первичная авторизация:
```
POST /anchor/anchorManage/doLogin (или аналог)
Content-Type: application/x-www-form-urlencoded
Body: account=LOGIN&password=PASSWORD
```
Получаем cookie `PHPSESSID`.

**Шаг 2** — вход в агентство (второй логин):
```
POST /anchor/anchorManage/doAgencyLogin (или аналог)
Body: aemail=AGENCY_EMAIL&apassword=AGENCY_PASSWORD
```
Получаем cookie `acuid`.

**Итоговые cookies для всех запросов:**
```
Cookie: PHPSESSID=xxx; acuid=xxx
```

**Обязательный заголовок для всех XHR запросов:**
```
X-Requested-With: XMLHttpRequest
```

### Если нужна 2FA (Google Authenticator)

После шага 2 сервер возвращает признак необходимости 2FA.
Затем:
```
POST /anchor/anchorManage/doTwoFactorAuth (предположительно)
Body: code=123456
```

### Хранение сессий

Сохранять `PHPSESSID` + `acuid` в PostgreSQL по agency_id.
При истечении — повторный логин автоматически.
Признак истечения: редирект на логин или код `{"code": -1}` в ответе.

---

## API эндпоинты Halo Live (подтверждены)

### 1. Список всех девушек (Host Infos)

```
GET /anchor/anchorManage/loadExtAnchorInfoList?page=1&limit=50&...
```

Возвращает поля (из реального ответа панели):
- `DisplayAccountId` — Halo ID девушки
- `AnchorName` — ник
- `Avatar` — URL аватара
- `Agent` — название агентства
- `ExtAgentSplitRatio` — процент (например 2000 = 20%)
- `DownRate` — коэффициент в профиле
- `RealDownRate` — коэффициент за последние 30 дней
- `MonthlyIncome` — заработок за месяц (в coins)
- `WeeklyIncome` — заработок за неделю (в coins)
- `PreIncome` — заработок за сутки (в coins)
- `MonthlyAvailable` — онлайн за месяц (строка, например "71h46m")
- `WeeklyAvailable` — онлайн за неделю
- `PreAvailable` — онлайн за сутки
- `MonthlyIncomeRanking` — место в топе приложения за месяц
- `AnchorGrade` — грейд (A, B, C, D, S)
- `Diamond` — текущий баланс
- `SplitDiamond` — баланс доступный для split
- `AccountId` — внутренний ID
- `Email` — email аккаунта
- `JudgeDate` — дата одобрения (ApprovalDate)
- `Fake` — процент фейковых фото (например "14.61%")
- `BanStatus` — статус бана (2 = активен, другое = заблокирован)
- `InAgent` — внутренний менеджер (Loren и т.д.)
- `ReceiveRate` — DislikeRate (если >= 0.4 — пропустить при split)

> ⚠️ Пагинация: параметры `page` и `limit`. Общее количество в поле `count`.

### 2. Онлайн-время (Live Duration)

```
POST /anchor/anchorManage/loadVisitorLiveDurationData
Body: page=1&limit=50&...
```

Дополнительные поля времени онлайн по дням.

### 3. Рейтинг агентств (Monthly Agency Rank)

```
POST /anchor/anchorManage/loadExtAgentRatingData
```

Данные рейтинга агентства за месяц.

### 4. Баланс агентства (Agency Wallet Details)

```
GET /anchor/anchorManage/loadAgencyWalletDetailList
```

Поля:
- Общий баланс
- Доступно к выводу
- В обработке
- Выведено за месяц

### 5. Монеты (Coins Record)

```
POST /anchor/anchorManage/loadAnchorCoinsRecords
Body: anchorId=ID&...
```

### 6. Баны (Ban Records)

```
POST /anchor/anchorManage/loadAnchorBanRecordsForVisitor
Body: anchorId=ID&...
```

---

## Экшн-эндпоинты (подтверждены)

### Изменить процент девушки

```
POST /anchor/anchorManage/setAgentRatio
Content-Type: application/x-www-form-urlencoded
Body: id=ANCHOR_ID&ratio=RATIO_VALUE&agent=AGENCY_NAME
```

- `id` — DisplayAccountId девушки
- `ratio` — значение * 100 (20% = 2000, 15% = 1500)
- `agent` — название агентства (например `TosAgency-Ukraine`)

Ответ: `{"code":0,"msg":"Operation successfully"}`

Ограничение: максимум 20% (ratio=2000).

### Split

```
POST /anchor/anchorManage/splitCoins
Content-Type: application/x-www-form-urlencoded
X-Requested-With: XMLHttpRequest
Body: ids=DISPLAY_ACCOUNT_ID
```

Одна девушка за один запрос. Split делать последовательно, не параллельно.

**Обязательные куки:**
```
PHPSESSID=xxx
acuid=xxx
trusted_device=xxx
acuemail=xxx
acudate=xxx
```

**Успешный ответ:** `{"code": 0, "msg": "Operation successfully"}`
**Ошибка сессии:** `{"code": -1}` или редирект → повторить логин.

**Условия пропуска девушки:**
- `SplitDiamond < 100` — баланс для сплита меньше 100 coins
- `float(ReceiveRate) >= 0.4` — коэффициент дизлайков 0.4 и выше

**Логика обхода:**
```python
for anchor in anchors:
    if anchor["SplitDiamond"] < 100:
        continue
    if float(anchor["ReceiveRate"]) >= 0.4:
        continue
    response = session.post(
        "https://admin.livegirl.me/anchor/anchorManage/splitCoins",
        data={"ids": anchor["DisplayAccountId"]},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    result = response.json()
    if result["code"] == 0:
        log("success", anchor)
    else:
        log("error", anchor, result)
```

**Пагинация:** Общее количество в поле `count`. При 356 девушках и `limit=50` — 8 запросов (page=1..8).

---

## База данных PostgreSQL

### Таблица agencies
```sql
id, name, url, account, password, aemail, apassword,
tfa_required, phpsessid, acuid, session_updated_at, is_active
```

### Таблица hosts (кеш данных девушек)
```sql
id, agency_id, display_account_id, nickname, avatar_url,
agent_name, ratio, down_rate, real_down_rate,
monthly_income, last_day_income,
last_month_online, last_day_online,
balance_coins, email, account_id, anchor_grade,
monthly_income_ranking, approval_date, updated_at
```

### Таблица users (CRM-пользователи)
```sql
id, username, password_hash, role (superadmin/admin),
created_at, last_login, is_active
```

### Таблица user_agency_access
```sql
user_id, agency_id,
can_view, can_split, can_change_ratio
```

### Таблица security_logs
```sql
id, user_id, action, ip_address, user_agent, created_at
```

### Таблица action_log (история изменений)
```sql
id, user_id, agency_id, action_type (ratio_change/split),
anchor_id, old_value, new_value, status, created_at, error_message
```

---

## Backend — FastAPI

### Структура

```
backend/
  main.py
  config.py
  database.py
  models/          # SQLAlchemy модели
  schemas/         # Pydantic схемы
  routers/
    auth.py        # /login, /logout, /me
    agencies.py    # CRUD агентств
    hosts.py       # список девушек, изменение %
    split.py       # split endpoint
    users.py       # управление CRM-пользователями
    sync.py        # ручное обновление данных
  services/
    halo_parser.py    # клиент Halo Live API
    session_manager.py  # управление сессиями
    scheduler.py      # автообновление каждые 15 мин
  auth/
    jwt.py         # JWT токены
    totp.py        # Google Authenticator 2FA
```

### Ключевые endpoints API

```
POST /auth/login
POST /auth/verify-2fa
GET  /auth/me

GET  /agencies          — список агентств (для текущего юзера)
POST /agencies          — добавить агентство (superadmin)
PUT  /agencies/{id}     — редактировать
DELETE /agencies/{id}   — удалить

GET  /hosts             — список девушек (с фильтрами и пагинацией)
POST /hosts/{id}/ratio  — изменить процент
GET  /hosts/{id}/history — история изменений

POST /split             — выполнить split (по агентству или всем)
GET  /split/history     — история split операций

GET  /users             — список CRM-пользователей (superadmin)
POST /users             — создать пользователя
PUT  /users/{id}        — изменить права
DELETE /users/{id}

POST /sync              — принудительная синхронизация
GET  /dashboard/stats   — суммарная статистика для карточек
```

---

## Frontend — Next.js

### Страницы

```
/login             — авторизация + 2FA
/dashboard         — дашборд с карточками и таблицей
/hosts             — таблица девушек
/risk              — только девушки в зоне риска
/agencies          — управление агентствами
/split             — страница split
/admins            — управление CRM-пользователями
/logs              — история действий
/settings          — настройки
```

### Компоненты

```
AgencyTabs         — верхнее меню агентств
StatsCards         — карточки дашборда (заработок, онлайн, риски)
HostsTable         — таблица с сортировкой и фильтрами
RatioEditor        — inline редактирование процента
RiskBadge          — статус риска (✅/⚠️/🚨)
GradeLevel         — уровень девушки (S/A/B/C/D)
SplitModal         — модальное окно split
```

---

## Логика уровней и риска (совпадает с ботом)

```python
def get_grade(monthly_income: int) -> str:
    if monthly_income >= 45000: return "S"
    if monthly_income >= 20000: return "A"
    if monthly_income >= 7000:  return "B"
    if monthly_income >= 2000:  return "C"
    return "D"

GRADE_LIMITS = {"S": None, "A": 0.25, "B": 0.18, "C": 0.18, "D": 0.12}

def check_risk(grade, down_rate, real_down_rate) -> list:
    risks = []
    if down_rate >= 0.18:
        risks.append("Коэффициент в профиле выше 0.18")
    limit = GRADE_LIMITS.get(grade)
    if limit and real_down_rate >= limit:
        risks.append(f"Коэффициент за 30 дней превышает лимит уровня {grade} ({limit})")
    return risks
```

> ⚠️ Уровень считается по `MonthlyIncome` из API, а НЕ по полю `AnchorGrade`.

---

## Конвертация coins → USD

```
20 coins = 1 USD
dollars = coins / 20
```

---

## Автообновление данных

- Scheduler каждые 15 минут делает `loadExtAnchorInfoList` для всех агентств
- Сохраняет в таблицу `hosts`
- Фронт показывает "Данные обновлены X мин. назад"
- Кнопка "Обновить данные" — принудительный вызов sync endpoint

---

## Безопасность

- JWT токены (access 15 мин + refresh 7 дней)
- 2FA через pyotp (Google Authenticator)
- Хэширование паролей bcrypt
- CORS только для своего домена
- Все действия логируются в security_logs и action_log
- HTTPS обязательно (certbot + nginx)

---

## Деплой

```
Ubuntu 22.04+ VDS
nginx (reverse proxy + SSL)
PostgreSQL 15
systemd сервисы: crm-backend.service
Node.js для Next.js (или next build + nginx static)
```

---

## Что нужно от заказчика

1. Логины/пароли от всех агентств
2. Google Authenticator seed (если есть 2FA)
3. Финальные макеты (есть на скриншоте, можно использовать как основу)
4. Доступ к VDS для деплоя

---

## Что неизвестно / нужно уточнить

| Вопрос | Статус |
|---|---|
| Логин эндпоинты (шаг 1 и 2) | ⚠️ Не захвачены, нужно проверить |
| Параметры пагинации loadExtAnchorInfoList | ✅ page, limit, count |
| Формат response при SESSION_EXPIRED | ✅ редирект или code=-1 |
| BanStatus значения | ✅ 2 = активен, другое = заблокирован |
| Split эндпоинт | ✅ /anchor/anchorManage/splitCoins |
