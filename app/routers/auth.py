"""
POST /api/auth/request-link  → envía magic link al email
POST /api/auth/verify        → verifica token, devuelve JWT
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.auth import create_jwt, create_magic_token
from app.core.config import settings
from app.core.deps import DB
from app.models.models import AuthToken, Company, LearningPath, User, UserPathProgress, UserRole, ProgressStatus
from app.schemas.auth import AuthResponse, MagicLinkRequest, MagicLinkResponse, VerifyTokenRequest

# Emails that automatically get admin role on first login
ADMIN_EMAILS = {"admin@admin.app"}

router = APIRouter()


@router.post("/request-link", response_model=MagicLinkResponse)
async def request_magic_link(body: MagicLinkRequest, db: DB):
    # Buscar o crear usuario
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None:
        # Check if the email domain belongs to an active company → auto-register
        auto_company = None
        if "@" in body.email:
            domain = body.email.split("@")[1].lower()
            domain_result = await db.execute(
                select(Company).where(
                    Company.email_domain == domain,
                    Company.is_active.is_(True),
                ).limit(1)
            )
            auto_company = domain_result.scalar_one_or_none()

        if auto_company is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Pedí tu acceso vía quickconsultora@gmail.com",
            )

        # Auto-register: create user linked to the matched company
        display_name = (body.full_name or "").strip() or body.email.split("@")[0].capitalize()
        user = User(
            email=body.email.lower(),
            full_name=display_name,
            role=UserRole.learner,
            company_id=auto_company.id,
            industry=auto_company.industry,
            experience_level="beginner",
            email_verified=False,
            onboarding_done=False,
        )
        db.add(user)
        await db.flush()

        # Assign the company's published onboarding path (if any)
        onb_path_result = await db.execute(
            select(LearningPath).where(
                LearningPath.company_id == auto_company.id,
                LearningPath.is_published.is_(True),
            ).limit(1)
        )
        onb_path = onb_path_result.scalar_one_or_none()
        if onb_path:
            db.add(UserPathProgress(
                user_id=user.id,
                path_id=onb_path.id,
                status=ProgressStatus.in_progress,
                started_at=datetime.now(timezone.utc),
            ))
            # Journey-type paths keep onboarding_done=False (user sees the journey screen first)
            if not (onb_path.industry and onb_path.industry.startswith("onboarding_")):
                user.onboarding_done = True
        await db.flush()

    else:
        # Existing user — ensure admin emails always have admin role
        if body.email.lower() in ADMIN_EMAILS and user.role == UserRole.learner:
            user.role = UserRole.admin
            user.onboarding_done = True
            if not user.company_id:
                first_company_result = await db.execute(
                    select(Company).where(Company.is_active.is_(True)).order_by(Company.name).limit(1)
                )
                first_company = first_company_result.scalar_one_or_none()
                if first_company:
                    user.company_id = first_company.id
                    user.industry = first_company.industry

        # Auto-associate company by email domain if not yet linked
        if user.company_id is None and "@" in body.email:
            domain = body.email.split("@")[1].lower()
            domain_result = await db.execute(
                select(Company).where(
                    Company.email_domain == domain,
                    Company.is_active.is_(True),
                ).limit(1)
            )
            matched_company = domain_result.scalar_one_or_none()
            if matched_company:
                user.company_id = matched_company.id
                user.industry = matched_company.industry

        # Existing non-admin user with onboarding not done → recover from pre-seeded state
        if not user.onboarding_done and body.email.lower() not in ADMIN_EMAILS:
            path_check_result = await db.execute(
                select(UserPathProgress, LearningPath)
                .join(LearningPath, UserPathProgress.path_id == LearningPath.id)
                .where(UserPathProgress.user_id == user.id)
                .limit(1)
            )
            row = path_check_result.first()
            if row is not None:
                _, assigned_path_obj = row
                # Journey-type paths (industry starts with "onboarding_") keep onboarding_done=False
                # so the user lands on the /onboarding-journey screen first.
                if not (assigned_path_obj.industry and assigned_path_obj.industry.startswith("onboarding_")):
                    user.onboarding_done = True
            elif user.company_id:
                # Check if company has an onboarding path and assign it
                onb_path_result = await db.execute(
                    select(LearningPath).where(
                        LearningPath.company_id == user.company_id,
                        LearningPath.industry == "onboarding",
                        LearningPath.is_published.is_(True),
                    ).limit(1)
                )
                onb_path = onb_path_result.scalar_one_or_none()
                if onb_path:
                    db.add(UserPathProgress(
                        user_id=user.id,
                        path_id=onb_path.id,
                        status=ProgressStatus.in_progress,
                        started_at=datetime.now(timezone.utc),
                    ))
                    user.onboarding_done = True
                    await db.flush()

    # Crear magic link token
    token = create_magic_token()
    auth_token = AuthToken(
        user_id=user.id,
        token=token,
        token_type="magic_link",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.MAGIC_LINK_EXPIRE_MINUTES),
    )
    db.add(auth_token)
    await db.commit()

    # En modo demo: auto-verificar y devolver JWT directo
    # En producción con email configurado, enviar el magic link por email
    auth_token.used_at = datetime.now(timezone.utc)
    user.email_verified = True
    is_new = not user.onboarding_done
    await db.commit()

    jwt_token = create_jwt(user.id)

    return MagicLinkResponse(
        message="Sesión iniciada.",
        access_token=jwt_token,
        user_id=str(user.id),
        is_new_user=is_new,
        onboarding_done=user.onboarding_done,
        role=user.role.value,
    )


@router.post("/verify", response_model=AuthResponse)
async def verify_token(body: VerifyTokenRequest, db: DB):
    result = await db.execute(
        select(AuthToken).where(
            AuthToken.token == body.token,
            AuthToken.token_type == "magic_link",
            AuthToken.used_at.is_(None),
        )
    )
    auth_token = result.scalar_one_or_none()

    if auth_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalido o ya utilizado")

    if auth_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado")

    # Marcar como usado
    auth_token.used_at = datetime.now(timezone.utc)

    # Verificar email del usuario
    user_result = await db.execute(select(User).where(User.id == auth_token.user_id))
    user = user_result.scalar_one()
    is_new = not user.email_verified
    user.email_verified = True
    await db.commit()

    jwt_token = create_jwt(user.id)

    return AuthResponse(
        access_token=jwt_token,
        user_id=str(user.id),
        is_new_user=is_new,
        onboarding_done=user.onboarding_done,
        role=user.role.value,
    )
