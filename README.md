# BionicPRO — Reports & Security Service

Проектная работа 9 спринта. Реализует два задания:
- **Задание 1:** Безопасность (PKCE Code Grant, Keycloak, BFF-паттерн)
- **Задание 2:** Сервис отчётов (ETL через Apache Airflow, ClickHouse, Reports API)

## Структура репозитория

```
├── docs/                        # Диаграммы C4 (draw.io)
│   ├── c4_security_architecture.drawio
│   └── c4_etl_reports_architecture.drawio
├── frontend/                    # React SPA (PKCE + кнопка отчёта)
├── reports-api/                 # FastAPI — эндпоинт GET /reports
├── airflow/                     # Apache Airflow ETL DAG
│   └── dags/etl_reports_dag.py
├── keycloak/
│   └── realm-export.json        # Конфигурация realm (PKCE, роли, пользователи)
├── scripts/
│   ├── init_clickhouse.ps1      # Инициализация ClickHouse (Windows)
│   └── init_clickhouse.sh       # Инициализация ClickHouse (Linux/Mac)
└── docker-compose.yaml
```

---

## Запуск

### 1. Запустить все сервисы

```bash
docker-compose up -d --build
```

Это поднимет весь стек:

| Сервис | URL | Описание |
|--------|-----|----------|
| Keycloak | http://localhost:8080 | SSO (admin: `admin` / `admin`) |
| Frontend | http://localhost:3000 | React SPA |
| Reports API | http://localhost:8000 | FastAPI |
| ClickHouse | http://localhost:8123 | OLAP БД |
| Airflow UI | http://localhost:8081 | ETL (admin: `admin` / `admin`) |
| CRM DB | localhost:5434 | PostgreSQL — источник CRM |
| Telemetry DB | localhost:5435 | PostgreSQL — источник телеметрии |

> **Keycloak** стартует ~40–60 секунд (ожидает healthcheck PostgreSQL).  
> **Airflow** стартует после того, как будут готовы все БД и ClickHouse — это ещё ~30–60 секунд.

### 2. Дождаться завершения ETL

DAG **`bionicpro_etl_reports`** запускается **автоматически** примерно через 30–60 секунд после старта стека — сервис `airflow-trigger` триггерит его сразу, как только поднимается scheduler.

DAG выполнит три шага:
1. `extract_crm` — извлечь данные клиентов и протезов из CRM PostgreSQL
2. `extract_telemetry` — извлечь телеметрию из Telemetry PostgreSQL
3. `transform` → `load_to_clickhouse` — объединить и загрузить в `bionicpro.report_mart`

После завершения DAG данные доступны через Reports API и фронтенд.

> Статус выполнения можно отследить в Airflow UI: http://localhost:8081 (`admin` / `admin`)

---

## Проверка работы

### Keycloak (PKCE)

```bash
curl http://localhost:8080/realms/reports-realm/.well-known/openid-configuration
```
Ожидаемо: JSON с `"code_challenge_methods_supported":["S256"]`

### Reports API

```bash
curl http://localhost:8000/health
```
Ожидаемо: `{"status":"ok"}`

### ClickHouse

```bash
curl http://localhost:8123/ping
```
Ожидаемо: `Ok.`

### Frontend — сценарий проверки

1. Открыть http://localhost:3000
2. Нажать **Login** → откроется Keycloak (PKCE flow с `code_challenge_method=S256`)
3. Войти как `prothetic1` / `prothetic123`
4. Нажать **Generate Report**
5. Ожидаемо: таблица с отчётом по протезу

### Проверка ограничения доступа

```bash
curl -i http://localhost:8000/reports
```
Ожидаемо: `401 Unauthorized`

---

## Тестовые пользователи

| Логин | Пароль | Роль | Доступ к отчётам |
|-------|--------|------|-----------------|
| `prothetic1` | `prothetic123` | `prothetic_user` | ✅ |
| `prothetic2` | `prothetic123` | `prothetic_user` | ✅ |
| `prothetic3` | `prothetic123` | `prothetic_user` | ✅ |
| `user1` | `password123` | `user` | ❌ |
| `admin1` | `admin123` | `administrator` | ❌ |

---


## Остановка

```bash
docker-compose down
```
