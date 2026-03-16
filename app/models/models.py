"""
SalesLeap — Modelos SQLAlchemy (mapean 1:1 con schema.sql)
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Text, Numeric,
    ForeignKey, ARRAY, Enum as SAEnum, Index, DateTime, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    learner = "learner"
    manager = "manager"
    admin = "admin"
    superadmin = "superadmin"


class ProgressStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class LessonType(str, enum.Enum):
    theory = "theory"
    quiz = "quiz"
    roleplay = "roleplay"
    challenge = "challenge"


# ── Empresas ──────────────────────────────────────────────────
class Company(Base):
    __tablename__ = "companies"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(200), nullable=False)
    slug         = Column(String(100), unique=True, nullable=False)
    email_domain = Column(String(100))
    logo_url     = Column(String(500))
    industry     = Column(String(50), nullable=False)
    plan         = Column(String(20), nullable=False, default="trial")
    plan_expires_at = Column(DateTime(timezone=True))
    is_active    = Column(Boolean, nullable=False, default=True)
    settings     = Column(JSONB, nullable=False, default={})
    created_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    users        = relationship("User", back_populates="company")
    documents    = relationship("CompanyDocument", back_populates="company")


# ── Usuarios ──────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email            = Column(String(255), unique=True, nullable=False)
    full_name        = Column(String(200), nullable=False)
    avatar_url       = Column(String(500))
    role             = Column(SAEnum(UserRole, name="user_role", create_type=False), nullable=False, default=UserRole.learner)
    company_id       = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    industry         = Column(String(50))
    experience_level = Column(String(20), default="beginner")
    total_xp         = Column(Integer, nullable=False, default=0)
    level            = Column(Integer, nullable=False, default=1)
    streak_current   = Column(Integer, nullable=False, default=0)
    streak_max       = Column(Integer, nullable=False, default=0)
    last_activity_at = Column(DateTime(timezone=True))
    is_active        = Column(Boolean, nullable=False, default=True)
    email_verified   = Column(Boolean, nullable=False, default=False)
    onboarding_done  = Column(Boolean, nullable=False, default=False)
    created_at       = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at       = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    company          = relationship("Company", back_populates="users")
    auth_tokens      = relationship("AuthToken", back_populates="user")
    badges           = relationship("UserBadge", back_populates="user")
    lesson_progress  = relationship("UserLessonProgress", back_populates="user")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token      = Column(String(255), unique=True, nullable=False)
    token_type = Column(String(20), nullable=False, default="magic_link")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at    = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user       = relationship("User", back_populates="auth_tokens")


# ── Contenido ─────────────────────────────────────────────────
class LearningPath(Base):
    __tablename__ = "learning_paths"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title        = Column(String(200), nullable=False)
    description  = Column(Text)
    industry     = Column(String(50), nullable=False)
    level        = Column(String(20), nullable=False, default="beginner")
    company_id   = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    cover_url    = Column(String(500))
    xp_reward    = Column(Integer, nullable=False, default=100)
    order_index  = Column(Integer, nullable=False, default=0)
    is_published = Column(Boolean, nullable=False, default=False)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    modules      = relationship("Module", back_populates="path", order_by="Module.order_index")


class Module(Base):
    __tablename__ = "modules"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_id           = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    title             = Column(String(200), nullable=False)
    description       = Column(Text)
    order_index       = Column(Integer, nullable=False, default=0)
    xp_reward         = Column(Integer, nullable=False, default=50)
    estimated_minutes = Column(Integer, nullable=False, default=10)
    is_published      = Column(Boolean, nullable=False, default=False)
    source_document   = Column(Text)
    created_at        = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at        = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    path              = relationship("LearningPath", back_populates="modules")
    lessons           = relationship("Lesson", back_populates="module", order_by="Lesson.order_index")


class Lesson(Base):
    __tablename__ = "lessons"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id         = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title             = Column(String(200), nullable=False)
    lesson_type       = Column(SAEnum(LessonType, name="lesson_type", create_type=False), nullable=False, default=LessonType.theory)
    content           = Column(JSONB, nullable=False, default={})
    order_index       = Column(Integer, nullable=False, default=0)
    xp_reward         = Column(Integer, nullable=False, default=20)
    estimated_minutes = Column(Integer, nullable=False, default=5)
    is_published      = Column(Boolean, nullable=False, default=False)
    created_at        = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    module            = relationship("Module", back_populates="lessons")


# ── Progreso ──────────────────────────────────────────────────
class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id      = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status         = Column(SAEnum(ProgressStatus, name="progress_status", create_type=False), nullable=False, default=ProgressStatus.not_started)
    score          = Column(Numeric(5, 2))
    attempts       = Column(Integer, nullable=False, default=0)
    time_spent_sec = Column(Integer, nullable=False, default=0)
    ai_feedback    = Column(Text)
    completed_at   = Column(DateTime(timezone=True))
    created_at     = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at     = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user           = relationship("User", back_populates="lesson_progress")
    lesson         = relationship("Lesson")


# ── Gamificación ──────────────────────────────────────────────
class Badge(Base):
    __tablename__ = "badges"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(100), nullable=False)
    description = Column(Text)
    icon        = Column(String(10))
    category    = Column(String(50), nullable=False)
    criteria    = Column(JSONB, nullable=False, default={})
    xp_bonus    = Column(Integer, nullable=False, default=0)
    rarity      = Column(String(20), nullable=False, default="common")
    created_at  = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id  = Column(UUID(as_uuid=True), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    context   = Column(JSONB, default={})

    user      = relationship("User", back_populates="badges")
    badge     = relationship("Badge")


class DailyStreak(Base):
    __tablename__ = "daily_streaks"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_date = Column(Date, nullable=False)
    xp_earned     = Column(Integer, nullable=False, default=0)
    lessons_done  = Column(Integer, nullable=False, default=0)
    created_at    = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


# ── Documentos empresa ────────────────────────────────────────
class CompanyDocument(Base):
    __tablename__ = "company_documents"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id        = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    uploaded_by       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    title             = Column(String(200), nullable=False)
    file_url          = Column(String(500), nullable=False)
    file_type         = Column(String(20))
    status            = Column(String(20), nullable=False, default="pending")
    generated_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id"))
    processed_at      = Column(DateTime(timezone=True))
    created_at        = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    company           = relationship("Company", back_populates="documents")


# ── Onboarding ───────────────────────────────────────────────
class OnboardingResult(Base):
    __tablename__ = "onboarding_results"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id            = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    industry_detected  = Column(String(50))
    level_detected     = Column(String(20))
    answers            = Column(JSONB, nullable=False, default=[])
    suggested_path_ids = Column(ARRAY(UUID(as_uuid=True)))
    completed_at       = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user               = relationship("User")


# ── Quiz Sessions ────────────────────────────────────────────
class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id       = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="SET NULL"))
    session_type    = Column(String(20), nullable=False, default="lesson")
    total_questions = Column(Integer, nullable=False, default=0)
    correct_answers = Column(Integer, nullable=False, default=0)
    score           = Column(Numeric(5, 2))
    xp_earned       = Column(Integer, nullable=False, default=0)
    started_at      = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at    = Column(DateTime(timezone=True))


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id     = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_index = Column(Integer, nullable=False)
    question_text  = Column(Text, nullable=False)
    user_answer    = Column(Text, nullable=False)
    correct_answer = Column(Text)
    is_correct     = Column(Boolean)
    ai_feedback    = Column(Text)
    answered_at    = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


# ── Notificaciones ───────────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type       = Column(String(50), nullable=False)
    title      = Column(String(200), nullable=False)
    body       = Column(Text)
    is_read    = Column(Boolean, nullable=False, default=False)
    payload    = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


# ── Path Progress ────────────────────────────────────────────
class UserPathProgress(Base):
    __tablename__ = "user_path_progress"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    path_id      = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    status       = Column(SAEnum(ProgressStatus, name="progress_status", create_type=False), nullable=False, default=ProgressStatus.not_started)
    started_at   = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    xp_earned    = Column(Integer, nullable=False, default=0)
