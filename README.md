# SalesLeap — Backend API

## Stack
- **FastAPI** + Python 3.12
- **PostgreSQL** (asyncpg) — schema completo en `schema.sql`
- **Redis** — sesiones, rankings en tiempo real
- **Claude API** — motor de IA (evaluación, coaching, generación de contenido)
- **Celery** — procesamiento async de documentos empresariales

## Estructura
```
salesleap/
├── app/
│   ├── main.py              # FastAPI app + routers
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   ├── database.py      # Async SQLAlchemy engine
│   │   ├── auth.py          # JWT + magic link helpers
│   │   └── deps.py          # Dependencias FastAPI (get_current_user, etc.)
│   ├── models/
│   │   └── models.py        # SQLAlchemy models (todos)
│   ├── schemas/             # Pydantic schemas (request/response)
│   ├── routers/             # Endpoints por dominio
│   │   ├── auth.py          # POST /auth/request-link, /auth/verify
│   │   ├── onboarding.py    # POST /onboarding/quiz, GET /onboarding/suggestions
│   │   ├── users.py         # GET/PUT /users/me, GET /users/{id}/stats
│   │   ├── companies.py     # CRUD empresas, subida de documentos
│   │   ├── paths.py         # GET /paths (filtrado por industria/nivel)
│   │   ├── modules.py       # GET /modules/{id}
│   │   ├── lessons.py       # GET /lessons/{id}, POST /lessons/{id}/complete
│   │   ├── progress.py      # GET /progress/me, GET /progress/company/{id}
│   │   ├── gamification.py  # GET /gamification/leaderboard, /badges
│   │   └── ai_coach.py      # POST /coach/chat, POST /coach/evaluate
│   └── services/
│       ├── ai_coach.py      # Claude API calls (YA IMPLEMENTADO)
│       ├── gamification.py  # Lógica XP, badges, streaks
│       ├── email.py         # Magic links via SMTP
│       └── document.py      # Ingesta PDF → módulos
├── schema.sql               # Schema PostgreSQL completo (YA HECHO)
├── requirements.txt         # Dependencias (YA HECHO)
└── .env.example             # Variables de entorno necesarias
```

## Para implementar con Claude Code

### Paso 1: Setup inicial
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completar variables
```

### Paso 2: Database
```bash
psql -U postgres -c "CREATE DATABASE salesleap;"
psql -U postgres -d salesleap -f schema.sql
```

### Paso 3: Correr
```bash
uvicorn app.main:app --reload
```

## Archivos pendientes para Claude Code
Los siguientes archivos están definidos en estructura pero necesitan implementación:

1. `app/core/database.py` — async engine + session
2. `app/core/auth.py` — generar/verificar magic links + JWT
3. `app/core/deps.py` — `get_current_user`, `get_db`
4. `app/schemas/` — schemas Pydantic para cada router
5. `app/routers/auth.py` — magic link flow completo
6. `app/routers/onboarding.py` — quiz nivelatorio + llamada a `ai_coach.generate_onboarding_suggestion()`
7. `app/routers/lessons.py` — completar lección + guardar progreso + trigger gamification
8. `app/services/gamification.py` — dar XP, verificar badges, actualizar streak
9. `app/services/document.py` — procesar PDF → llamar `ai_coach.generate_module_from_document()`

## Lógica de auth empresarial
Si el email del usuario es `@toyota.com.ar` y existe una empresa con `email_domain = "toyota.com.ar"`,
el usuario se asocia automáticamente a esa empresa y accede a su contenido exclusivo.

## Endpoints críticos del MVP
- `POST /api/auth/request-link` → manda magic link al email
- `POST /api/auth/verify` → verifica token, devuelve JWT
- `POST /api/onboarding/quiz` → evalúa respuestas con Claude, devuelve nivel + rutas sugeridas
- `GET /api/paths?industry=auto&level=beginner` → rutas disponibles
- `POST /api/lessons/{id}/complete` → marca como completada, da XP, verifica badges
- `POST /api/coach/chat` → chat libre con el coach IA
- `GET /api/gamification/leaderboard?company_id={id}` → ranking de la empresa
