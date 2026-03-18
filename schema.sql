-- ============================================================
-- SalesLeap — Schema SQL completo v1.0
-- ============================================================

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- EMPRESAS
-- ============================================================
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,          -- toyota-cba, remax-cordoba
    email_domain    VARCHAR(100),                          -- @toyota.com.ar → acceso exclusivo
    logo_url        VARCHAR(500),
    industry        VARCHAR(50) NOT NULL,                  -- auto | inmobiliaria | b2b | otro
    plan            VARCHAR(20) NOT NULL DEFAULT 'trial',  -- trial | pro | enterprise
    plan_expires_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    settings        JSONB NOT NULL DEFAULT '{}',           -- config personalizada por empresa
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_companies_email_domain ON companies(email_domain) WHERE email_domain IS NOT NULL;
CREATE INDEX idx_companies_industry ON companies(industry);

-- ============================================================
-- USUARIOS
-- ============================================================
CREATE TYPE user_role AS ENUM ('learner', 'manager', 'admin', 'superadmin');

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    avatar_url      VARCHAR(500),
    role            user_role NOT NULL DEFAULT 'learner',
    company_id      UUID REFERENCES companies(id) ON DELETE SET NULL,
    industry        VARCHAR(50),                           -- auto | inmobiliaria | b2b | otro
    experience_level VARCHAR(20) DEFAULT 'beginner',      -- beginner | intermediate | advanced
    -- Gamificación
    total_xp        INTEGER NOT NULL DEFAULT 0,
    level           INTEGER NOT NULL DEFAULT 1,
    streak_current  INTEGER NOT NULL DEFAULT 0,
    streak_max      INTEGER NOT NULL DEFAULT 0,
    last_activity_at TIMESTAMPTZ,
    -- Auth
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    onboarding_done BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_xp ON users(total_xp DESC);

-- Tokens de auth (magic link)
CREATE TABLE auth_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(255) UNIQUE NOT NULL,
    token_type  VARCHAR(20) NOT NULL DEFAULT 'magic_link', -- magic_link | refresh
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auth_tokens_token ON auth_tokens(token);
CREATE INDEX idx_auth_tokens_user ON auth_tokens(user_id);

-- ============================================================
-- CONTENIDO: RUTAS, MÓDULOS Y LECCIONES
-- ============================================================
CREATE TABLE learning_paths (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    industry    VARCHAR(50) NOT NULL,                      -- para qué rubro es
    level       VARCHAR(20) NOT NULL DEFAULT 'beginner',
    company_id  UUID REFERENCES companies(id) ON DELETE CASCADE, -- NULL = contenido global
    cover_url   VARCHAR(500),
    xp_reward   INTEGER NOT NULL DEFAULT 100,
    order_index INTEGER NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_paths_industry ON learning_paths(industry);
CREATE INDEX idx_paths_company ON learning_paths(company_id);

CREATE TABLE modules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    path_id         UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    order_index     INTEGER NOT NULL DEFAULT 0,
    xp_reward       INTEGER NOT NULL DEFAULT 50,
    estimated_minutes INTEGER NOT NULL DEFAULT 10,
    is_published    BOOLEAN NOT NULL DEFAULT FALSE,
    source_document TEXT,                                  -- doc original que usó Claude para generar
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_modules_path ON modules(path_id);

CREATE TYPE lesson_type AS ENUM ('theory', 'quiz', 'roleplay', 'challenge');

CREATE TABLE lessons (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_id       UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    title           VARCHAR(200) NOT NULL,
    lesson_type     lesson_type NOT NULL DEFAULT 'theory',
    content         JSONB NOT NULL DEFAULT '{}',           -- contenido estructurado generado por Claude
    order_index     INTEGER NOT NULL DEFAULT 0,
    xp_reward       INTEGER NOT NULL DEFAULT 20,
    estimated_minutes INTEGER NOT NULL DEFAULT 5,
    is_published    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lessons_module ON lessons(module_id);

-- ============================================================
-- PROGRESO DE USUARIOS
-- ============================================================
CREATE TYPE progress_status AS ENUM ('not_started', 'in_progress', 'completed');

CREATE TABLE user_path_progress (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    path_id     UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    status      progress_status NOT NULL DEFAULT 'not_started',
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    xp_earned   INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, path_id)
);

CREATE TABLE user_lesson_progress (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id       UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    status          progress_status NOT NULL DEFAULT 'not_started',
    score           NUMERIC(5,2),                          -- 0-100 para quizzes
    attempts        INTEGER NOT NULL DEFAULT 0,
    time_spent_sec  INTEGER NOT NULL DEFAULT 0,
    ai_feedback     TEXT,                                  -- feedback generado por Claude
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, lesson_id)
);

CREATE INDEX idx_lesson_progress_user ON user_lesson_progress(user_id);
CREATE INDEX idx_lesson_progress_lesson ON user_lesson_progress(lesson_id);

-- ============================================================
-- QUIZ
-- ============================================================
CREATE TABLE quiz_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id       UUID REFERENCES lessons(id) ON DELETE SET NULL,
    session_type    VARCHAR(20) NOT NULL DEFAULT 'lesson', -- lesson | onboarding | challenge
    total_questions INTEGER NOT NULL DEFAULT 0,
    correct_answers INTEGER NOT NULL DEFAULT 0,
    score           NUMERIC(5,2),
    xp_earned       INTEGER NOT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE quiz_answers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_index  INTEGER NOT NULL,
    question_text   TEXT NOT NULL,
    user_answer     TEXT NOT NULL,
    correct_answer  TEXT,
    is_correct      BOOLEAN,
    ai_feedback     TEXT,                                  -- explicación de Claude por qué era correcta/incorrecta
    answered_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_quiz_answers_session ON quiz_answers(session_id);

-- ============================================================
-- GAMIFICACIÓN: BADGES Y STREAKS
-- ============================================================
CREATE TABLE badges (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    icon        VARCHAR(10),                               -- emoji o código de ícono
    category    VARCHAR(50) NOT NULL,                      -- onboarding | streak | completion | score | social
    criteria    JSONB NOT NULL DEFAULT '{}',               -- condiciones para ganarlo
    xp_bonus    INTEGER NOT NULL DEFAULT 0,
    rarity      VARCHAR(20) NOT NULL DEFAULT 'common',     -- common | rare | epic | legendary
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_badges (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id    UUID NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    context     JSONB DEFAULT '{}',                        -- info de por qué lo ganó
    UNIQUE(user_id, badge_id)
);

CREATE INDEX idx_user_badges_user ON user_badges(user_id);

CREATE TABLE daily_streaks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    xp_earned   INTEGER NOT NULL DEFAULT 0,
    lessons_done INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, activity_date)
);

CREATE INDEX idx_streaks_user ON daily_streaks(user_id);
CREATE INDEX idx_streaks_date ON daily_streaks(activity_date);

-- ============================================================
-- ONBOARDING QUIZ NIVELATORIO
-- ============================================================
CREATE TABLE onboarding_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    industry_detected   VARCHAR(50),
    level_detected      VARCHAR(20),
    answers             JSONB NOT NULL DEFAULT '[]',       -- respuestas crudas
    suggested_path_ids  UUID[],                            -- paths sugeridas por Claude
    completed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- CONTENIDO EMPRESA: DOCUMENTOS SUBIDOS
-- ============================================================
CREATE TABLE company_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    uploaded_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    title           VARCHAR(200) NOT NULL,
    file_url        VARCHAR(500) NOT NULL,
    file_type       VARCHAR(20),                           -- pdf | docx | txt
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending | processing | done | error
    generated_path_id UUID REFERENCES learning_paths(id),  -- path generada a partir del doc
    processed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_company_docs_company ON company_documents(company_id);

-- ============================================================
-- NOTIFICACIONES
-- ============================================================
CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL,                      -- badge_earned | streak_at_risk | new_module | etc
    title       VARCHAR(200) NOT NULL,
    body        TEXT,
    is_read     BOOLEAN NOT NULL DEFAULT FALSE,
    payload     JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- ============================================================
-- FUNCIÓN: actualizar updated_at automáticamente
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_companies_updated BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_paths_updated BEFORE UPDATE ON learning_paths FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_modules_updated BEFORE UPDATE ON modules FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_lesson_progress_updated BEFORE UPDATE ON user_lesson_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- DATOS INICIALES: Badges del sistema
-- ============================================================
INSERT INTO badges (name, description, icon, category, criteria, xp_bonus, rarity) VALUES
('Primer paso',     'Completaste tu primera lección',           '🚀', 'onboarding',   '{"lessons_completed": 1}',     50,  'common'),
('En racha x3',     '3 días seguidos de actividad',             '🔥', 'streak',        '{"streak_days": 3}',           75,  'common'),
('En racha x7',     '7 días seguidos de actividad',             '⚡', 'streak',        '{"streak_days": 7}',           150, 'rare'),
('En racha x30',    '30 días seguidos de actividad',            '💎', 'streak',        '{"streak_days": 30}',          500, 'legendary'),
('Perfeccionista',  'Obtuviste 100% en un quiz',                '🎯', 'score',         '{"quiz_score": 100}',          100, 'rare'),
('Módulo completo', 'Terminaste tu primer módulo',              '📚', 'completion',    '{"modules_completed": 1}',     100, 'common'),
('Ruta completa',   'Terminaste una ruta de aprendizaje',       '🏆', 'completion',    '{"paths_completed": 1}',       300, 'epic'),
('Vendedor Pro',    'Completaste 5 rutas de aprendizaje',       '⭐', 'completion',    '{"paths_completed": 5}',       1000,'legendary'),
('Veloz',           'Completaste una lección en menos de 3 min','⚡', 'speed',         '{"lesson_under_seconds": 180}',50,  'rare'),
('Bienvenido',      'Completaste el quiz de nivelación',        '👋', 'onboarding',    '{"onboarding_done": true}',    100, 'common'),
('Orientado',      'Completaste el mapa del área en tu primer día', '🗺️', 'onboarding', '{"onboarding_lesson": "El mapa del área"}',              75,  'common'),
('En acción',      'Completaste tu primer ticket real',             '⚙️', 'onboarding', '{"onboarding_lesson": "Primer ticket real"}',            100, 'rare'),
('Especialista',   'Certificado como Operador Junior',              '🎓', 'onboarding', '{"onboarding_lesson": "Certificación: Operador Junior"}', 150, 'epic');
