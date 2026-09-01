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

## Deploy gratis: Google Cloud Run + Supabase

Alternativa sin costo para demos. Cloud Run corre el `Dockerfile` tal cual y
escala a cero; su free tier (2M requests/mes) no expira. Supabase aporta el
Postgres.

---

### Paso 1 — Crear el proyecto en Supabase

1. [supabase.com](https://supabase.com) → **New project**, plan **Free**.
2. **Region:** elegir la misma que vaya a usar Cloud Run (ej. `us-east-1` con
   `us-east1`). Cada consulta cruza esa distancia; con regiones distintas se
   pagan 100ms+ por request.
3. **Database password:** generarla y guardarla — se muestra una sola vez y va
   dentro de `DATABASE_URL`.

El proyecto tarda un par de minutos en aprovisionarse.

---

### Paso 2 — Sacar la connection string correcta

**Connect** (arriba en el dashboard) ofrece tres opciones. La elección importa:

| Opción | Puerto | Sirve acá |
|---|---|---|
| **Session pooler** | 5432 | ✅ **Usar esta** |
| Transaction pooler | 6543 | Funciona, pero desactiva prepared statements |
| Direct connection | 5432 | ❌ Es IPv6-only; Cloud Run sale por IPv4 |

Copiar la de **Session pooler**. Tiene esta forma:

```
postgresql://postgres.abcdefghijklm:TU_PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres
             └──────┬──────────────┘
                el usuario incluye el project-ref: no es sólo "postgres"
```

**Por qué el session pooler y no el de transacción:** el dialecto asyncpg de
SQLAlchemy usa `prepare()` para toda sentencia. Un pooler en modo transacción
multiplexa varios clientes sobre la misma conexión del servidor, y los nombres
que asyncpg asigna en orden numérico chocan entre sí:

```
asyncpg.exceptions.DuplicatePreparedStatementError
```

El session pooler da una conexión dedicada por cliente y no tiene ese
problema. Con `--max-instances 2` y `DB_POOL_SIZE=5` son 10 conexiones como
mucho — muy por debajo del límite del tier gratuito.

Si aun así hace falta el de transacción (muchas instancias en paralelo),
`app/core/database.py` lo detecta por el puerto 6543 y aplica solo la
configuración que necesita: nombres únicos de prepared statement, cachés en
cero y `NullPool`. Con un pooler en otro puerto, forzarlo con
`DB_TRANSACTION_POOLER=true`.

---

### Paso 3 — Adaptar la URL al driver async

Dos cambios sobre lo que copiaste:

```diff
- postgresql://postgres.abcdefghijklm:PASS@aws-0-us-east-1.pooler.supabase.com:5432/postgres
+ postgresql+asyncpg://postgres.abcdefghijklm:PASS@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```

1. `postgresql://` → **`postgresql+asyncpg://`** (sin esto SQLAlchemy busca el
   driver sincrónico y no arranca).
2. El `?sslmode=require` es opcional pero recomendado: `build_engine_kwargs()`
   lo traduce a la config TLS que asyncpg entiende. **No hace falta sacarlo**
   si venía en la URL — asyncpg lo rechazaría como parámetro y la app no
   levantaría, y justamente por eso el código lo intercepta.

Si la password tiene caracteres especiales (`@`, `/`, `:`, `#`), hay que
URL-encodearlos: `@` → `%40`, `/` → `%2F`, `#` → `%23`.

---

### Paso 4 — Crear el schema

No hay que hacer nada: en el primer arranque `AUTO_SEED=auto` detecta la base
vacía, aplica `schema.sql` y siembra las 4 empresas demo con sus usuarios y
progreso. Los arranques siguientes la detectan poblada y saltean.

Para hacerlo a mano y ver los errores en el momento: **SQL Editor** →
pegar `schema.sql` → **Run**.

Verificar en **Table Editor**: tienen que aparecer 16 tablas y `companies` con
6 filas después del primer arranque de la app.

---

### Paso 5 — Deploy en Cloud Run

Las variables van en un archivo YAML, no inline: `DATABASE_URL` puede contener
comas y otros caracteres que `gcloud` interpreta como separadores, y así
además no quedan secretos en el historial del shell.

Crear `.env.yaml` en la raíz (ya está en `.gitignore`):

```yaml
ENVIRONMENT: production
AUTO_SEED: auto
WEB_CONCURRENCY: "1"
DB_POOL_SIZE: "5"
DATABASE_URL: postgresql+asyncpg://postgres.REF:PASS@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
SECRET_KEY: generar-con-openssl-rand-hex-32
ANTHROPIC_API_KEY: sk-ant-...
```

Los valores numéricos van entre comillas: el YAML los convertiría a int y
`gcloud` espera strings.

```bash
gcloud run deploy salesleap \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --max-instances 2 \
  --env-vars-file .env.yaml
```

`--max-instances 2` acota las conexiones a la base: cada instancia abre su
propio pool de `DB_POOL_SIZE`.

El primer deploy tarda varios minutos — construye la imagen entera, incluido
el `npm run build` del frontend.

### Paso 6 — Verificar

```bash
curl https://TU-SERVICIO-xxxx.run.app/health
```

```json
{"status":"ok","service":"salesleap-api","spa":true}
```

- **`"spa": true`** → el frontend quedó dentro de la imagen; `/login` anda.
- **`"spa": false`** → el build de la imagen no incluyó `web/dist`.

Después, en los logs de Cloud Run tiene que aparecer una sola vez:

```
startup: schema.sql applied
startup: base content seeded
startup: seed-agro (agro.app) applied
```

Y en los arranques siguientes:

```
startup: database already has 6 companies — skipping seed
```

Último paso: agregar la URL del servicio a `CORS_ORIGINS` y redeployar.

Login de prueba: cualquier email `@agro.app`, `@auto.app` o `@admin.app`
(ver `DEMO_PROFILES.md`).

---

### Problemas frecuentes

| Síntoma | Causa |
|---|---|
| `InvalidPasswordError` | La password tiene caracteres especiales sin URL-encodear, o se usó el usuario `postgres` en vez de `postgres.PROJECT_REF` que pide el pooler |
| `TypeError: connect() got an unexpected keyword argument 'sslmode'` | La app corre con una versión anterior a este cambio — actualizar |
| `DuplicatePreparedStatementError` | Se está usando el pooler de transacción en un puerto distinto de 6543: setear `DB_TRANSACTION_POOLER=true` |
| `ConnectionDoesNotExistError` / timeouts | Se usó la Direct connection (IPv6). Cambiar al session pooler |
| `Network is unreachable` | Lo mismo: IPv6 |
| El seed no corrió y las tablas están vacías | `AUTO_SEED=never`, o el schema se aplicó a mano y `companies` quedó con filas |

### Notas del tier gratuito

- **Supabase Free se pausa** tras 7 días sin actividad. Los datos quedan, pero
  el proyecto se apaga hasta reactivarlo desde el dashboard. Con Cloud Run
  escalando a cero no hay nada que la mantenga despierta: para una demo que
  tiene que estar viva, conviene un ping periódico.
- **Cloud Run exige tarjeta** en la cuenta de GCP, aunque no cobre dentro del
  free tier.
- Alternativa sin tarjeta: **Render free**, pero duerme a los 15 minutos y
  tarda ~1 minuto en despertar — hay que precalentarlo antes de una demo.

---

## Troubleshooting

### Error: "connection refused" a PostgreSQL
- Verificá que `DATABASE_URL` tiene el prefijo `postgresql+asyncpg://`
- Verificá que las variables de referencia `${{Postgres.*}}` están bien

### Error: "no module named app"
- Verificá que Railway está usando el Dockerfile (no Nixpacks)
- En **Settings** → **Builder** → seleccionar **Dockerfile**

### GET /login (o cualquier ruta del SPA) devuelve 404

El backend sirve el frontend desde `static/`. Si esa carpeta no está en la
imagen, el catch-all no se registra y toda ruta que no sea de la API da 404.

- `curl https://TU-APP/health` → si responde `"spa": false`, la imagen no
  tiene el frontend buildeado.
- **Settings** → **Builder** → seleccionar **Dockerfile**: la stage
  `fe-builder` corre `npm run build` y copia `web/dist` a `static/`.
- El log de arranque también lo avisa: `SPA catch-all NOT registered`.

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
