"""
POST /api/onboarding/quiz        → evalúa respuestas con Claude, devuelve nivel + rutas sugeridas
GET  /api/onboarding/suggestions → rutas sugeridas del onboarding previo
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.models import LearningPath, OnboardingResult
from app.schemas.onboarding import OnboardingQuizRequest, OnboardingQuizResponse
from app.services import ai_coach

router = APIRouter()


@router.post("/quiz", response_model=OnboardingQuizResponse)
async def submit_onboarding_quiz(body: OnboardingQuizRequest, db: DB, user: CurrentUser):
    if user.onboarding_done:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Onboarding ya completado")

    # Llamar a Claude para evaluar
    suggestion = await ai_coach.generate_onboarding_suggestion(
        answers=[a.model_dump() for a in body.answers],
        industry=body.industry,
        experience_years=body.experience_years,
    )

    # Buscar paths que matcheen con los temas prioritarios y la industria
    result = await db.execute(
        select(LearningPath).where(
            LearningPath.industry == body.industry,
            LearningPath.level == suggestion["level"],
            LearningPath.is_published.is_(True),
            # Paths globales o de la empresa del usuario
            (LearningPath.company_id.is_(None)) | (LearningPath.company_id == user.company_id),
        ).limit(5)
    )
    paths = result.scalars().all()
    suggested_ids = [p.id for p in paths]

    # Guardar resultado de onboarding
    onboarding = OnboardingResult(
        user_id=user.id,
        industry_detected=body.industry,
        level_detected=suggestion["level"],
        answers=[a.model_dump() for a in body.answers],
        suggested_path_ids=suggested_ids,
    )
    db.add(onboarding)

    # Actualizar perfil del usuario
    user.industry = body.industry
    user.experience_level = suggestion["level"]
    user.onboarding_done = True
    await db.commit()

    return OnboardingQuizResponse(
        level=suggestion["level"],
        strengths=suggestion["strengths"],
        gaps=suggestion["gaps"],
        priority_topics=suggestion["priority_topics"],
        explanation=suggestion["explanation"],
        quick_win_tip=suggestion["quick_win_tip"],
        suggested_path_ids=suggested_ids,
    )


@router.get("/suggestions")
async def get_onboarding_suggestions(db: DB, user: CurrentUser):
    result = await db.execute(
        select(OnboardingResult).where(OnboardingResult.user_id == user.id).order_by(OnboardingResult.completed_at.desc())
    )
    onboarding = result.scalar_one_or_none()
    if onboarding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No completaste el onboarding aun")

    # Traer las paths sugeridas
    if onboarding.suggested_path_ids:
        paths_result = await db.execute(
            select(LearningPath).where(LearningPath.id.in_(onboarding.suggested_path_ids))
        )
        paths = paths_result.scalars().all()
    else:
        paths = []

    return {
        "level": onboarding.level_detected,
        "industry": onboarding.industry_detected,
        "suggested_paths": [
            {"id": str(p.id), "title": p.title, "description": p.description, "level": p.level}
            for p in paths
        ],
    }
