# SalesLeap — Perfiles de Demo y Funcionalidades

> Referencia completa para demos y ventas. Refleja el estado actual del sistema (marzo 2026).

---

## Índice

1. [Perfiles de usuario](#1-perfiles-de-usuario)
2. [Empresas del sistema](#2-empresas-del-sistema)
3. [Rutas de aprendizaje](#3-rutas-de-aprendizaje)
4. [Funcionalidades por perfil](#4-funcionalidades-por-perfil)
5. [Flujo de autenticación](#5-flujo-de-autenticación)
6. [Motor de gamificación](#6-motor-de-gamificación)
7. [Coach IA](#7-coach-ia)
8. [Panel de administración](#8-panel-de-administración)
9. [Endpoints clave de la API](#9-endpoints-clave-de-la-api)
10. [Cómo inicializar cada demo](#10-cómo-inicializar-cada-demo)

---

## 1. Perfiles de usuario

### 1.1 `admin@admin.app` — Administrador de plataforma

| Campo           | Valor                              |
|-----------------|------------------------------------|
| **Rol**         | `admin`                            |
| **Empresa**     | SalesLeap Demo (`admin.app`)       |
| **Contraseña**  | —  (usa magic link / auto-login)   |
| **onboarding**  | Completado (saltea el quiz)        |

**Qué puede hacer:**
- Accede directamente al panel de administración tras el login
- Ve el resumen semanal de todo el equipo SalesLeap Demo: lecciones completadas esta semana, racha y XP de cada vendedor
- Consulta el leaderboard global por empresa
- Navega las rutas de aprendizaje disponibles
- Gestiona empresas y usuarios (endpoints admin)

**Cómo se configura:** está hardcodeado en `ADMIN_EMAILS` dentro de `auth.py`. Al hacer login, el sistema le asigna automáticamente `role = admin` y `onboarding_done = True`, sin pasar por el quiz inicial.

---

### 1.2 `lucas@admin.app` — Lucas García ⭐ Star performer

| Campo               | Valor                        |
|---------------------|------------------------------|
| **Rol**             | `learner`                    |
| **Empresa**         | SalesLeap Demo               |
| **Ruta asignada**   | Venta Consultiva Automotriz  |
| **Perfil de datos** | Alto rendimiento             |

**Datos sembrados:**
- 8 lecciones completadas (5 esta semana, 3 semanas anteriores)
- Racha activa: **4 días**
- Score por lección: 70–100
- XP: alto (~350–450 XP estimados)
- Nivel 1 (en progreso hacia nivel 2)
- Último acceso: hace 1–4 horas

**Para qué sirve en demo:** demuestra cómo se ve un vendedor comprometido y activo en el panel del manager.

---

### 1.3 `andres@admin.app` — Andrés Martínez 📊 Rendimiento medio

| Campo               | Valor                        |
|---------------------|------------------------------|
| **Rol**             | `learner`                    |
| **Empresa**         | SalesLeap Demo               |
| **Ruta asignada**   | Venta Consultiva Automotriz  |
| **Perfil de datos** | Rendimiento moderado         |

**Datos sembrados:**
- 5 lecciones completadas (2 esta semana, 3 semanas anteriores)
- Racha activa: **1 día**
- XP: medio (~175–250 XP estimados)
- Último acceso: hace 1–4 horas

**Para qué sirve en demo:** muestra un vendedor regular que cumple sin destacar. Contrasta bien con Lucas en el panel del manager.

---

### 1.4 `kun@admin.app` — Sergio Agüero 🔴 Bajo rendimiento

| Campo               | Valor                        |
|---------------------|------------------------------|
| **Rol**             | `learner`                    |
| **Empresa**         | SalesLeap Demo               |
| **Ruta asignada**   | Venta Consultiva Automotriz  |
| **Perfil de datos** | Inactivo                     |

**Datos sembrados:**
- 2 lecciones completadas (0 esta semana)
- Sin racha activa (0 días)
- XP: bajo (~60–90 XP estimados)
- Último acceso: hace 3–7 días

**Para qué sirve en demo:** resalta el problema que resuelve SalesLeap — visibilidad de quién no está entrenando. Ideal para mostrar alertas de inactividad y cómo el manager puede intervenir.

---

### 1.5 `nuevo@industria.app` — Nuevo operador (onboarding)

| Campo               | Valor                                          |
|---------------------|------------------------------------------------|
| **Rol**             | `learner`                                      |
| **Empresa**         | Industria Demo (`industria.app`)               |
| **Ruta asignada**   | Onboarding Operativo — Industria Demo          |
| **onboarding**      | Auto-completado al primer login                |

**Comportamiento al primer login:**
1. El sistema detecta que el dominio `@industria.app` tiene una empresa con ruta `industry = "onboarding"`
2. Auto-asigna la ruta de onboarding operativo
3. Marca `onboarding_done = True` → va directo al dashboard (no ve el quiz genérico)
4. Encuentra su viaje de 7 días estructurado en 3 niveles

**Ruta asignada — Onboarding Operativo Industria Demo:**

| Nivel                  | Módulo                    | Lecciones                                                                 | XP   |
|------------------------|---------------------------|---------------------------------------------------------------------------|------|
| Nivel 1 — Explorador   | Recepción y orientación   | "Bienvenida a la planta" (theory, 30xp) + "El mapa del área" (challenge, 40xp) 🗺️ | 70   |
| Nivel 2 — Operador     | Gestión de tickets        | "El ciclo del ticket" (quiz, 50xp) + "Primer ticket real" (challenge, 60xp) ⚙️   | 110  |
| Nivel 3 — Especialista | Diagnóstico avanzado      | "Diagnóstico de proceso" (roleplay, 70xp) + "Certificación: Operador Junior" (challenge, 80xp) 🎓 | 150 |

**Badges desbloqueables:**
- 🗺️ **Orientado** (common, +75 XP) — al completar "El mapa del área"
- ⚙️ **En acción** (rare, +100 XP) — al completar "Primer ticket real"
- 🎓 **Especialista** (epic, +150 XP) — al completar "Certificación: Operador Junior"

**Para qué sirve en demo:** demuestra el onboarding gamificado para empresas industriales/operativas. Muestra cómo un nuevo empleado recibe su plan estructurado desde el día 1, sin configuración manual.

---

---

### 1.6 `pablo@auto.app` — Pablo (Vendedor Auto Demo)

| Campo               | Valor                              |
|---------------------|------------------------------------|
| **Rol**             | `learner`                          |
| **Empresa**         | Auto Demo (`auto.app`)             |
| **Ruta asignada**   | Venta Consultiva Automotriz        |
| **onboarding**      | Completado                         |

**Para qué sirve en demo:** perfil vendedor base de la demo automotriz. Puede navegar el dashboard, hacer lecciones y ver su progreso.

---

### 1.7 `admin@auto.app` — Manager Auto Demo

| Campo           | Valor                          |
|-----------------|--------------------------------|
| **Rol**         | `manager`                      |
| **Empresa**     | Auto Demo (`auto.app`)         |
| **onboarding**  | Completado                     |

**Qué puede hacer:**
- Accede directo al panel de administración tras el login
- Ve el resumen semanal del equipo Auto Demo (Lucas, Sergio, Andrés, Laura)
- Consulta lecciones completadas, rachas y XP de cada vendedor

---

### 1.8 `lucas@auto.app` — Lucas García ⭐ Star performer

| Campo               | Valor                              |
|---------------------|------------------------------------|
| **Rol**             | `learner`                          |
| **Empresa**         | Auto Demo                          |
| **Perfil de datos** | Alto rendimiento                   |

**Datos sembrados:**
- 10 lecciones completadas (5 esta semana)
- Racha activa: **5 días** / Racha máxima: 12 días
- Badges: Primer Paso, En Racha, Perfeccionista

---

### 1.9 `sergio@auto.app` — Sergio Ramírez 📊 Rendimiento medio-alto

| Campo               | Valor                              |
|---------------------|------------------------------------|
| **Rol**             | `learner`                          |
| **Empresa**         | Auto Demo                          |
| **Perfil de datos** | Rendimiento moderado               |

**Datos sembrados:**
- 7 lecciones completadas (3 esta semana)
- Racha activa: **3 días** / Racha máxima: 6 días
- Badges: Primer Paso, En Racha

---

### 1.10 `andres@auto.app` — Andrés López 🔶 Rendimiento bajo-medio

| Campo               | Valor                              |
|---------------------|------------------------------------|
| **Rol**             | `learner`                          |
| **Empresa**         | Auto Demo                          |
| **Perfil de datos** | Bajo-moderado                      |

**Datos sembrados:**
- 4 lecciones completadas (1 esta semana)
- Racha activa: **1 día** / Racha máxima: 3 días
- Badges: Primer Paso

---

### 1.11 `laura@auto.app` — Laura Martínez 🔴 Recién iniciada

| Campo               | Valor                              |
|---------------------|------------------------------------|
| **Rol**             | `learner`                          |
| **Empresa**         | Auto Demo                          |
| **Perfil de datos** | Sin actividad reciente             |

**Datos sembrados:**
- 1 lección completada (0 esta semana)
- Sin racha activa / Racha máxima: 1 día
- Badges: Primer Paso

**Para qué sirve en demo:** resalta el problema que resuelve SalesLeap — visibilidad de quién no está entrenando. Contrasta fuerte con Lucas.

---

### 1.12 `admin@industria.app` — Manager Industria Demo

| Campo           | Valor                                |
|-----------------|--------------------------------------|
| **Rol**         | `manager`                            |
| **Empresa**     | Industria Demo (`industria.app`)     |
| **onboarding**  | Completado                           |

**Qué puede hacer:**
- Accede al panel de su empresa
- Ve el progreso de todos los empleados de Industria Demo
- Consulta métricas semanales del equipo (endpoint `/api/progress/company/{id}/weekly`, requiere rol `manager` o superior)
- Ve el leaderboard filtrado por empresa

**Para qué sirve en demo:** muestra la perspectiva del supervisor que monitorea el onboarding de sus empleados en tiempo real.

---

## 2. Empresas del sistema

| Nombre              | Dominio            | Industria      | ID (UUID)                                   | Plan |
|---------------------|--------------------|----------------|---------------------------------------------|------|
| Toyota Córdoba      | toyotacba.com.ar   | auto           | `a0000000-0000-0000-0000-000000000001`      | pro  |
| RE/MAX Córdoba      | remaxcba.com.ar    | inmobiliaria   | `a0000000-0000-0000-0000-000000000002`      | pro  |
| SalesLeap Demo      | admin.app          | auto           | `a0000000-0000-0000-0000-000000000099`      | pro  |
| Industria Demo      | industria.app      | manufactura    | `a0000000-0000-0000-0000-000000000003`      | pro  |
| Auto Demo           | auto.app           | auto           | `a0000000-0000-0000-0000-000000000004`      | pro  |

**Comportamiento por dominio:** cuando un usuario nuevo se registra con un email cuyo dominio coincide con `email_domain` de una empresa activa, el sistema lo asocia automáticamente a esa empresa y hereda su industria.

---

## 3. Rutas de aprendizaje

### 3.1 Venta Consultiva Automotriz (global)
- **ID:** `b0000000-0000-0000-0000-000000000001`
- **Industria:** auto
- **Nivel:** beginner
- **Empresa:** sin asignar (disponible para todos)
- **XP total:** 500

| # | Módulo                              | Lecciones (4 c/u)                                                                  |
|---|-------------------------------------|------------------------------------------------------------------------------------|
| 1 | Recepción y Detección de Necesidades | Theory + Quiz (SPIN) + Roleplay + Challenge                                       |
| 2 | Presentación y Test Drive           | Theory (CPB) + Quiz + Roleplay + Challenge                                         |
| 3 | Cierre y Negociación                | Theory + Quiz + Roleplay + Challenge                                               |

### 3.2 Cierre Inmobiliario Profesional (global)
- **ID:** `b0000000-0000-0000-0000-000000000002`
- **Industria:** inmobiliaria
- **Nivel:** beginner
- **Empresa:** sin asignar
- **XP total:** 500

| # | Módulo                              | Lecciones (4 c/u)                                                                  |
|---|-------------------------------------|------------------------------------------------------------------------------------|
| 1 | Captación de Propiedades            | Theory + Quiz + Roleplay + Challenge                                               |
| 2 | Calificación de Compradores         | Theory + Quiz + Roleplay + Challenge                                               |
| 3 | Negociación y Cierre                | Theory + Quiz + Roleplay + Challenge                                               |

### 3.3 Onboarding Operativo — Industria Demo (exclusivo)
- **ID:** `b0000000-0000-0000-0000-000000000003`
- **Industria:** onboarding (tipo especial — gatilla auto-asignación)
- **Empresa:** Industria Demo (solo para `@industria.app`)
- **XP total:** 330 (sin contar bonos de badges)

| # | Módulo                    | IDs de módulo                              | Lecciones                                                                      |
|---|---------------------------|--------------------------------------------|--------------------------------------------------------------------------------|
| 1 | Recepción y orientación   | `c0000000-0000-0000-0000-000000000007`     | Bienvenida a la planta + El mapa del área                                      |
| 2 | Gestión de tickets        | `c0000000-0000-0000-0000-000000000008`     | El ciclo del ticket + Primer ticket real                                        |
| 3 | Diagnóstico avanzado      | `c0000000-0000-0000-0000-000000000009`     | Diagnóstico de proceso + Certificación: Operador Junior                        |

---

## 4. Funcionalidades por perfil

### Learner (vendedor / operador)

| Funcionalidad                    | Descripción                                                                          |
|----------------------------------|--------------------------------------------------------------------------------------|
| **Dashboard personalizado**      | Ve su misión diaria (meta: 3 lecciones/día), progreso de su ruta y próxima lección  |
| **Lecciones interactivas**       | 4 tipos: teoría, quiz, roleplay y challenge (ver sección 3.4)                        |
| **XP y niveles**                 | Cada lección completada otorga XP; al acumular 500 XP sube de nivel                 |
| **Racha diaria**                 | Contador de días consecutivos con actividad; visible en el dashboard                 |
| **Badges**                       | Colección de insignias desbloqueables por logros (ver sección 6)                    |
| **Leaderboard**                  | Ranking de la empresa por XP total                                                   |
| **Coach IA**                     | Chat libre con el asistente de ventas entrenado en su industria y nivel              |

### Manager / Admin de empresa

| Funcionalidad                    | Descripción                                                                          |
|----------------------------------|--------------------------------------------------------------------------------------|
| **Panel semanal del equipo**     | Lecciones por vendedor esta semana, meta cumplida (≥3 lecciones), racha, XP         |
| **% cumplimiento de objetivo**   | Qué porcentaje del equipo alcanzó la meta semanal                                    |
| **Usuarios activos**             | Cuántos miembros tuvieron actividad en la semana actual                              |
| **Leaderboard filtrado**         | Ranking por empresa, configurable por límite de usuarios                             |
| **Progreso total por empresa**   | Vista de todos los usuarios con lecciones completadas y XP acumulado                 |

### Admin de plataforma (`admin@admin.app`)

Hereda todo lo de Manager, más:
- Acceso a todas las empresas
- Endpoints de inicialización y seed de datos
- Gestión de rutas, módulos y lecciones

---

## 5. Flujo de autenticación

SalesLeap usa **Magic Link + JWT** en modo demo auto-verificado:

```
POST /api/auth/request-link  { "email": "...", "full_name": "..." }
```

**Flujo completo:**

```
Usuario ingresa email
       ↓
¿Existe el usuario en la BD?
  NO → ❌ HTTP 403: "Pedí tu acceso vía quickconsultora@gmail.com"
       (solo pueden entrar usuarios pre-registrados)

  SÍ → Usuario existente
       ↓
       ¿Email en ADMIN_EMAILS y role≠admin? → upgradear a admin
       ¿onboarding_done=False y no admin?
          ¿Tiene UserPathProgress? → onboarding_done=True (recuperación)
          ¿Empresa con ruta onboarding? → asignar ruta + onboarding_done=True
       ↓
Crear magic token (en demo: auto-usado)
Marcar email_verified=True
Generar JWT
       ↓
Respuesta: { access_token, user_id, is_new_user, onboarding_done }
```

**Respuesta clave:**
- `onboarding_done: true` → frontend manda al **dashboard**
- `onboarding_done: false` → frontend manda al **quiz de onboarding**

---

## 6. Motor de gamificación

### XP y niveles
- Cada lección completada otorga XP según su dificultad (`xp_reward` en la BD)
- Fórmula de nivel: `nivel = XP_total // 500 + 1`
- El XP se acumula en `users.total_xp`

### Racha diaria
- Se registra en la tabla `daily_streaks` (una fila por usuario por día)
- `users.streak_current` = días consecutivos activos
- `users.streak_max` = racha máxima histórica

### Misión diaria
- Meta: completar **3 lecciones por día**
- `GET /api/progress/mission` devuelve el estado actual y la próxima lección pendiente

### Badges (insignias)

**Tipos de criterios soportados:**

| Criterio              | Descripción                                             | Ejemplo                                        |
|-----------------------|---------------------------------------------------------|------------------------------------------------|
| `lessons_completed`   | Nº total de lecciones completadas                       | `{"lessons_completed": 10}`                    |
| `streak_days`         | Racha de días consecutivos                              | `{"streak_days": 7}`                           |
| `quiz_score`          | Puntaje mínimo en un quiz                               | `{"quiz_score": 100}`                          |
| `onboarding_done`     | Completó el onboarding                                  | `{"onboarding_done": true}`                    |
| `lesson_under_seconds`| Completó una lección en menos de N segundos             | `{"lesson_under_seconds": 60}`                 |
| `onboarding_lesson`   | Completó una lección específica del onboarding por título | `{"onboarding_lesson": "El mapa del área"}`  |

**Badges del sistema (base):**

| Badge            | Criterio                          | Rareza  | XP bonus |
|------------------|-----------------------------------|---------|----------|
| Primer Paso      | lessons_completed ≥ 1             | common  | 50       |
| En Racha         | streak_days ≥ 3                   | common  | 75       |
| Perfeccionista   | quiz_score = 100                  | rare    | 100      |
| Bienvenido       | onboarding_done = true            | common  | 25       |
| Flash            | lesson_under_seconds < 60         | epic    | 150      |

**Badges de onboarding Industria Demo:**

| Badge       | Lección gatillo                          | Rareza  | XP bonus |
|-------------|------------------------------------------|---------|----------|
| 🗺️ Orientado  | "El mapa del área"                      | common  | 75       |
| ⚙️ En acción  | "Primer ticket real"                    | rare    | 100      |
| 🎓 Especialista | "Certificación: Operador Junior"      | epic    | 150      |

### Leaderboard
```
GET /api/gamification/leaderboard?company_id={uuid}&limit=20
```
Devuelve ranking por `total_xp` descendente. Filtra por empresa si se pasa `company_id`.

### Badges del usuario
```
GET /api/gamification/badges
```
Devuelve **todos los badges del sistema** con `earned: true/false` y `earned_at` para el usuario actual.

---

## 7. Coach IA

Basado en Claude (Anthropic). Dos modos:

### Chat libre
```
POST /api/coach/chat
{ "message": "...", "conversation_history": [...] }
```
El coach conoce el nombre, industria, nivel de XP y racha del usuario. Responde como un mentor de ventas especializado.

### Evaluación de respuesta
```
POST /api/coach/evaluate
{ "question": "...", "user_answer": "...", "correct_answer": "..." }
```
Evalúa la respuesta del usuario en un quiz, explica por qué es correcta o incorrecta, y da un tip accionable.

---

## 8. Panel de administración

### Vista semanal del equipo
```
GET /api/progress/company/{company_id}/weekly
```
**Requiere:** rol `manager` o `admin`

Devuelve:
```json
{
  "week_start": "2026-03-16",
  "week_end": "2026-03-22",
  "total_users": 4,
  "active_this_week": 3,
  "completed_target": 2,
  "completed_target_pct": 50,
  "weekly_target": 3,
  "team": [
    {
      "full_name": "Lucas García",
      "lessons_this_week": 5,
      "total_lessons": 8,
      "streak_current": 4,
      "total_xp": 420,
      "level": 1,
      "met_weekly_target": true
    },
    ...
  ]
}
```

---

## 9. Endpoints clave de la API

| Método | Endpoint                                  | Auth        | Descripción                                    |
|--------|-------------------------------------------|-------------|------------------------------------------------|
| POST   | `/api/auth/request-link`                  | —           | Login con magic link (auto-verificado en demo) |
| POST   | `/api/onboarding/quiz`                    | JWT         | Enviar quiz inicial → asigna ruta + nivel      |
| GET    | `/api/progress/me`                        | JWT         | Progreso personal (XP, nivel, racha)           |
| GET    | `/api/progress/mission`                   | JWT         | Misión diaria + próxima lección                |
| GET    | `/api/progress/company/{id}/weekly`       | JWT Manager | Panel semanal del equipo                       |
| GET    | `/api/gamification/leaderboard`           | JWT         | Ranking por XP (filtrable por empresa)         |
| GET    | `/api/gamification/badges`                | JWT         | Todos los badges con earned: true/false        |
| POST   | `/api/coach/chat`                         | JWT         | Chat libre con el coach IA                     |
| POST   | `/api/coach/evaluate`                     | JWT         | Evaluación de respuesta de quiz                |
| GET    | `/api/paths`                              | JWT         | Rutas de aprendizaje disponibles               |
| GET    | `/api/paths/{id}/modules`                 | JWT         | Módulos de una ruta                            |
| POST   | `/api/lessons/{id}/complete`              | JWT         | Marcar lección como completada                 |

---

## 10. Cómo inicializar cada demo

Todos los endpoints de admin requieren el header `X-Admin-Key: {SECRET_KEY}`.

### ⚡ Inicialización automática (Railway)

**No se requiere ninguna acción manual.** Al iniciar la aplicación, el sistema ejecuta automáticamente `_auto_seed()` que siembra todos los datos en orden:

1. Schema SQL (tablas)
2. Contenido base (badges, rutas, módulos, lecciones)
3. Demo `admin.app` (SalesLeap Demo)
4. Demo `auto.app` (Auto Demo)
5. Demo `industria.app` (Industria Demo)

Cada paso es idempotente: si los datos ya existen, no se duplican.

### Demo 1 — Panel de manager con equipo de ventas (`admin.app`)

**Usuarios:** `admin@admin.app` (admin), `lucas@admin.app`, `andres@admin.app`, `kun@admin.app`

### Demo 2 — Auto Demo (`auto.app`)

**Usuarios:** `admin@auto.app` (manager), `pablo@auto.app`, `lucas@auto.app`, `sergio@auto.app`, `andres@auto.app`, `laura@auto.app`

### Demo 3 — Onboarding industrial (`industria.app`)

**Usuarios:** `admin@industria.app` (manager), `nuevo@industria.app`

---

## Tipos de lecciones

| Tipo        | Descripción                                                                      |
|-------------|----------------------------------------------------------------------------------|
| `theory`    | Contenido explicativo con puntos clave y resumen. El learner lee y avanza.       |
| `quiz`      | Preguntas de opción múltiple con respuesta correcta y explicación.               |
| `roleplay`  | Escenario situacional donde el learner responde como vendedor/operador. El Coach IA evalúa la respuesta. |
| `challenge` | Similar al quiz pero con framing de "desafío práctico". Más corto y directo.     |

---

*Documento generado: marzo 2026 — SalesLeap v1.0.0*
