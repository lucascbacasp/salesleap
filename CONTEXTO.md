# SalesLeap — Contexto del Proyecto

> Documento de referencia para retomar el proyecto sin perder contexto.
> Actualizar ante cada cambio arquitectónico relevante.

---

## Descripción del Producto

**SalesLeap** es un sistema de capacitación gamificada — el "Duolingo para vendedores y operarios de empresa".

El producto convierte el entrenamiento corporativo (ventas, inocuidad alimentaria, compliance, etc.) en una experiencia de microaprendizaje diario con:
- Misiones diarias (3 lecciones / día)
- Rachas de actividad (streaks)
- Puntos de experiencia (XP) y niveles
- Badges de logro y certificados descargables
- Panel de admin con métricas del equipo en tiempo real

**Casos de uso actuales:**
- Equipos de ventas B2B/B2C (industria auto, inmobiliaria)
- Operarios de planta bajo estándar BRCGS / BPM (módulo inocuidad alimentaria)
- Onboarding gamificado de 7 días para nuevos ingresos

---

## Stack Técnico Completo

### Backend
| Componente | Tecnología |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async + asyncpg) |
| Base de datos | PostgreSQL |
| Auth | Magic Link JWT (sin contraseñas) |
| AI Coach | Anthropic Claude API (`claude-3-haiku`) |
| Deploy | Railway (Docker vía `Procfile`) |
| Schema | `schema.sql` aplicado en cada startup |
| Seed | `_auto_seed()` idempotente en lifespan de FastAPI |

### Frontend
| Componente | Tecnología |
|---|---|
| Framework | React + Vite |
| Routing | React Router v6 |
| Estilos | Tailwind CSS (dark theme custom) |
| Estado auth | Context API + `localStorage` |
| HTTP | `fetch` con wrapper `api.js` |
| Build | `npm run build` → `web/dist/` servido por FastAPI |

### Infraestructura
- **Railway** — deploy automático desde `git push`
- **PostgreSQL** — provisto por Railway (variable `DATABASE_URL`)
- **Docker** — imagen de producción con build multi-stage (Node + Python)
- **Variables de entorno:** `DATABASE_URL`, `JWT_SECRET`, `ANTHROPIC_API_KEY`, `RESEND_API_KEY` (pendiente)

---

## Modelo de Negocio

### Precio al cliente
| Modalidad | Precio |
|---|---|
| Por usuario / mes | **USD 15** |
| Flat fee empresa (hasta 15 usuarios) | **USD 180 / mes** |

### Costos de API por tipo de usuario
| Perfil | Costo estimado / mes | Descripción |
|---|---|---|
| **Light** | USD 0,25 | Usa el coach < 5 veces / mes |
| **Baseline** | USD 1,00 | Uso típico, 1–2 sesiones / semana |
| **Heavy** | USD 2,50 | Power user, sesiones largas diarias |
| **Extreme** | USD 5,00 | Integración automática / bot |

**Margen bruto estimado:** ~93% en perfil baseline (USD 15 ingreso − USD 1 costo ≈ USD 14).

---

## Módulos Implementados

### 1. Auth — Magic Link
- `POST /api/auth/request-link` → genera token y devuelve JWT directo (modo demo sin email)
- `POST /api/auth/verify` → verifica token de link real
- Auto-registro por dominio de email: si `@empresa.com` coincide con `Company.email_domain`, el usuario se crea automáticamente y se asigna a esa empresa sin alta manual
- Roles: `learner`, `manager`, `admin`, `superadmin`
- Guard de acceso: emails no registrados y sin dominio de empresa → 403 con mensaje de contacto

### 2. Onboarding Gamificado — 7 días
- Flujo: login → detecta `onboarding_done = false` → `/onboarding-journey`
- Para paths tipo `onboarding_*`: muestra pantalla journey con bienvenida personalizada, barra de progreso, misión del día y lista completa de módulos/lecciones
- Para usuarios sin path asignado: redirige a `/onboarding` (quiz de industria / ventas)
- Al completar el path: `onboarding_done = true`, acceso pleno al dashboard

### 3. Sistema XP / Badges / Streaks
- **XP:** cada lección tiene `xp_reward` configurable; se acumula en `User.total_xp`
- **Niveles:** calculados por rangos de XP (Lvl 1–10+)
- **Streaks:** `DailyStreak` trackea días consecutivos de actividad
- **Badges:** `Badge` table con `criteria_type` (xp_threshold, lessons_count, path_complete, module_complete); se otorgan automáticamente al completar lecciones
- **Misión diaria:** 3 lecciones / día; `GET /api/progress/mission` devuelve estado + próxima lección

### 4. Panel Admin — Métricas del Equipo
- `GET /api/progress/company/{id}/weekly` → usuarios activos, lecciones, racha, XP, nivel
- `GET /api/progress/company/{id}/certificates` → estado de certificación por badge "Operario Habilitado"
- Vista `/admin`: tabla del equipo con columna **Certificado** (Pendiente / 🏅 Emitido)
- Modal de certificado: nombre, fecha de habilitación en español, módulos completados, puntaje XP
- Filtro: solo muestra `role = learner` (excluye managers y admins de la tabla)

### 5. Módulo Inocuidad Alimentaria — Servagrop (BRCGS)
**Empresa:** Servagrop | `email_domain: agro.app` | `industry: alimentaria`
**Path:** "Operario Habilitado — Inocuidad Alimentaria" | `industry: onboarding_alimentaria`

| Módulo | Lecciones | XP | Badge |
|---|---|---|---|
| Guardián de la inocuidad | Theory (30XP) + Quiz 6 preg. (40XP) | 70 XP | 🛡 Guardián de la inocuidad |
| Operador de puntos críticos | Theory (50XP) + Roleplay (60XP) | 110 XP | 🎯 CCP Operador |
| Operario habilitado | Challenge (50XP) + Quiz 8 preg. (70XP) | 120 XP | 🏅 Operario Habilitado |

**Certificado:** Al obtener el badge "Operario Habilitado", el admin puede ver el certificado digital desde el panel (nombre, fecha, módulos, XP final).

### 6. AI Coach
- `POST /api/coach/chat` → conversación con Claude (streaming)
- Contexto del usuario inyectado: XP, nivel, racha, path actual, última lección
- Modelo: `claude-3-haiku-20240307` (balance costo/calidad)
- Historial: últimos N turnos (pendiente fix a 10 turnos — ver Próximos Pasos)

---

## Usuarios de Demo

| Email | Rol | Empresa | Estado |
|---|---|---|---|
| `javier@agro.app` | learner | Servagrop | `onboarding_done=false` → journey inocuidad |
| `admin@agro.app` | manager | Servagrop | Panel admin con métricas + certificados |
| `nuevo@industria.app` | learner | industria.app | Onboarding genérico (quiz de ventas) |
| `admin@industria.app` | manager | industria.app | Panel admin industria |

**Auto-registro activo:** cualquier email `@agro.app` no registrado se crea automáticamente como learner de Servagrop al primer login.

---

## Arquitectura de Rutas (Frontend)

| Ruta | Componente | Acceso |
|---|---|---|
| `/login` | `Login.jsx` | Público |
| `/onboarding` | `Onboarding.jsx` | Autenticado — quiz de ventas / industria |
| `/onboarding-journey` | `OnboardingJourney.jsx` | Autenticado — journey con path asignado |
| `/dashboard` | `Dashboard.jsx` | Autenticado learner |
| `/path/:pathId` | `PathDetail.jsx` | Autenticado |
| `/lesson/:lessonId` | `LessonView.jsx` | Autenticado |
| `/coach` | `Coach.jsx` | Autenticado |
| `/admin` | `Admin.jsx` | Autenticado manager/admin |

**Lógica de redirección post-login:**
```
role admin/manager → /admin
onboarding_done = false → /onboarding-journey
onboarding_done = true  → /dashboard
```

---

## Endpoints API Principales

```
POST  /api/auth/request-link          # Login / auto-registro
POST  /api/auth/verify                # Verificar magic link token
GET   /api/users/me                   # Perfil del usuario autenticado
GET   /api/paths                      # Paths disponibles (filtro por industry)
GET   /api/paths/{id}/modules         # Módulos + lecciones de un path
GET   /api/progress/mission           # Misión del día + next_lesson
POST  /api/progress/lessons/{id}      # Completar lección (XP, badge, streak)
GET   /api/progress/company/{id}/weekly       # Métricas equipo (admin)
GET   /api/progress/company/{id}/certificates # Certificados (admin)
POST  /api/coach/chat                 # Chat con AI coach
GET   /api/gamification/leaderboard   # Ranking XP
```

---

## Seed y Deploy

### Seed automático en Railway
`_auto_seed()` corre en cada deploy (lifespan de FastAPI). Es **idempotente** — safe en cada redeploy.

Pasos:
1. Aplica `schema.sql`
2. Seed base content (companies + paths genéricos)
3. Seed-demo (`admin.app` — SalesLeap Demo)
4. Seed-auto (`auto.app` — Toyota Córdoba demo)
5. Seed-industria (`industria.app` — onboarding ventas)
6. Seed-agro (`agro.app` — Servagrop inocuidad alimentaria)

### Correr seed manualmente
```bash
python3 seed.py              # Solo seed Servagrop (idempotente)
python3 seed.py --full       # Full seed completo
```

### Deploy Railway
```bash
git push origin master       # Railway detecta el push y despliega
```

---

## Próximos Pasos Pendientes

| Prioridad | Tarea | Detalle |
|---|---|---|
| 🔴 Alta | **Deploy Railway — verificar en prod** | Confirmar que `_auto_seed()` corre bien con la nueva BD de Railway y los 6 pasos completan sin error |
| 🔴 Alta | **Email real con Resend** | Activar `RESEND_API_KEY` en Railway; implementar envío real del magic link en `request_magic_link()` en vez de auto-verificar |
| 🟡 Media | **Fix historial coach — 10 turnos** | El AI coach actualmente no limita el historial de conversación; implementar ventana de 10 turnos (20 mensajes) para controlar costos de API y evitar context overflow |
| 🟡 Media | **Tests de integración para seed-agro** | Agregar test que valide que `nuevo@agro.app` se auto-registra correctamente y queda asignado al path de inocuidad |
| 🟢 Baja | **Certificado PDF descargable** | Desde el modal del certificado, generar y descargar un PDF firmado con los datos del operario habilitado |
| 🟢 Baja | **Notificaciones push / email de racha** | Recordatorio diario si el usuario no completó su misión del día |
| 🟢 Baja | **Multi-idioma** | Base para inglés (mercado LATAM internacional) |

---

## Decisiones de Arquitectura Relevantes

- **Sin contraseñas:** Magic Link reduce fricción de onboarding y elimina riesgo de passwords débiles
- **Auto-registro por dominio:** Permite que el admin de Servagrop invite a su equipo solo diciéndoles "usá tu email `@agro.app`" — sin alta manual en el sistema
- **UPSERT en seed:** Todo el seed usa `ON CONFLICT DO UPDATE/NOTHING` → safe en redeployments sin `UniqueViolationError`
- **`industry` como tipo de path:** Permite distinguir paths de ventas (`auto`, `inmobiliaria`) de paths de onboarding genérico (`onboarding`) y especializados (`onboarding_alimentaria`) con la misma arquitectura
- **`onboarding_done` flag:** Controla el estado del flujo de bienvenida sin tabla extra; `false` → journey, `true` → dashboard
- **Panel admin filtra solo learners:** Managers y admins no aparecen en la tabla del equipo (`WHERE role = 'learner'`)
