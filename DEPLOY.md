# Deploy SalesLeap en Railway

## Arquitectura

```
┌─────────────────────────────────────────────┐
│                 Railway                      │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  App     │  │ Postgres │  │  Redis   │  │
│  │ (Docker) │→ │   16     │  │   7      │  │
│  │ :$PORT   │  │  :5432   │  │  :6379   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│       ↑                                      │
│   Public URL                                 │
│   salesleap-production.up.railway.app        │
└─────────────────────────────────────────────┘
```

---

## Paso 1: Crear proyecto en Railway

1. Ir a [railway.app](https://railway.app) y loguearse con GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Seleccionar el repo `lucascbacasp/salesleap`
4. Railway detecta el `Dockerfile` automáticamente

---

## Paso 2: Agregar PostgreSQL

1. En el proyecto, click **+ New** → **Database** → **Add PostgreSQL**
2. Railway crea la instancia y expone la variable `DATABASE_URL`
3. **IMPORTANTE**: Railway genera una URL con formato `postgresql://...`
   pero SalesLeap usa `asyncpg`, así que hay que cambiar el prefijo:

   En las variables del servicio **App**, agregar:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```
   Luego **editar manualmente** el valor para reemplazar:
   - `postgresql://` → `postgresql+asyncpg://`

   O usar la variable raw:
   ```
   DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
   ```

4. **Inicializar schema**: Conectarse a la DB con Railway CLI o desde la UI:
   ```bash
   railway run psql < schema.sql
   ```

---

## Paso 3: Agregar Redis

1. En el proyecto, click **+ New** → **Database** → **Add Redis**
2. Railway expone `REDIS_URL` automáticamente
3. En las variables del servicio **App**, agregar:
   ```
   REDIS_URL=${{Redis.REDIS_URL}}
   ```

---

## Paso 4: Variables de entorno

En el servicio **App** → **Variables**, configurar:

### Obligatorias

| Variable | Valor | Notas |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}` | Referencia a Postgres de Railway |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Referencia a Redis de Railway |
| `SECRET_KEY` | *(generar con `openssl rand -hex 32`)* | Para firmar JWTs |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Tu API key de Anthropic |

### Opcionales (para funcionalidad completa)

| Variable | Valor | Notas |
|---|---|---|
| `DEBUG` | `false` | No activar en prod |
| `CORS_ORIGINS` | `["https://tu-dominio.com"]` | Dominios del frontend |
| `SMTP_HOST` | `smtp.resend.com` | Para enviar magic links reales |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | `resend` | |
| `SMTP_PASS` | `re_...` | API key de Resend/Sendgrid/etc |
| `EMAIL_FROM` | `noreply@salesleap.app` | |
| `S3_BUCKET` | `salesleap-docs` | Para uploads de documentos |
| `S3_REGION` | `us-east-1` | |
| `AWS_ACCESS_KEY` | `AKIA...` | |
| `AWS_SECRET_KEY` | `...` | |

### Variables automáticas de Railway

| Variable | Descripción |
|---|---|
| `PORT` | Railway la inyecta automáticamente. El app la lee del entorno. |

---

## Paso 5: Inicializar la base de datos

### Opción A: Railway CLI

```bash
# Instalar CLI
npm install -g @railway/cli

# Login
railway login

# Linkear proyecto
railway link

# Ejecutar schema
railway run psql -f schema.sql

# Ejecutar seed (opcional, para datos de demo)
railway run python3 seed.py
```

### Opción B: Desde la UI de Railway

1. Ir al servicio **Postgres** → **Data** → **Query**
2. Copiar y pegar el contenido de `schema.sql`
3. Ejecutar

---

## Paso 6: Deploy

Railway hace deploy automático en cada push a `master`. Para forzar un redeploy:

```bash
railway up
```

### Verificar que funciona

```bash
# Health check
curl https://TU-APP.up.railway.app/health

# Debería responder:
# {"status":"ok","service":"salesleap-api"}
```

---

## Paso 7: Frontend (opcional)

El frontend en `web/` se puede deployar en:

### Opción A: Railway (static site)

Crear otro servicio en el mismo proyecto:
1. **+ New** → **GitHub Repo** → mismo repo
2. En **Settings**:
   - Root Directory: `web`
   - Build Command: `npm ci --legacy-peer-deps && npx vite build`
   - Start Command: `npx serve dist -s -l $PORT`
3. En **Variables**:
   - `VITE_API_URL=https://TU-BACKEND.up.railway.app`

### Opción B: Vercel (recomendado para SPA)

```bash
cd web
npx vercel --prod
```

Configurar en Vercel:
- Framework: Vite
- Build: `npm run build`
- Output: `dist`
- Environment variable: `VITE_API_URL=https://TU-BACKEND.up.railway.app`

---

## Troubleshooting

### Error: "connection refused" a PostgreSQL
- Verificá que `DATABASE_URL` tiene el prefijo `postgresql+asyncpg://`
- Verificá que las variables de referencia `${{Postgres.*}}` están bien

### Error: "no module named app"
- Verificá que Railway está usando el Dockerfile (no Nixpacks)
- En **Settings** → **Builder** → seleccionar **Dockerfile**

### Los magic links no llegan
- En desarrollo, los tokens se loguean a consola. Revisá los logs de Railway.
- Para enviar emails reales, configurá las variables SMTP.

### El schema no se ejecutó
- Ejecutá manualmente con `railway run psql -f schema.sql`
- Verificá que las extensiones `uuid-ossp` y `pgcrypto` están habilitadas

---

## Costos estimados (Railway)

| Servicio | Estimado/mes |
|---|---|
| App (512MB RAM) | ~$5 |
| PostgreSQL (1GB) | ~$5 |
| Redis (128MB) | ~$3 |
| **Total** | **~$13/mes** |

Railway incluye $5 de crédito gratis en el tier Hobby.
