"""
SalesLeap — AI Coach Service
Motor Claude que evalúa respuestas, genera feedback y crea contenido
"""
import anthropic
from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
MODEL = settings.CLAUDE_MODEL


async def evaluate_quiz_answer(
    question: str,
    user_answer: str,
    correct_answer: str,
    industry: str,
    user_level: str,
) -> dict:
    """
    Evalúa la respuesta de un quiz y devuelve feedback personalizado.
    Retorna: {is_correct, feedback, tip, score}
    """
    prompt = f"""Sos un coach de ventas experto en la industria de {industry}.
Un vendedor de nivel {user_level} respondió una pregunta de capacitación.

Pregunta: {question}
Respuesta correcta: {correct_answer}
Respuesta del vendedor: {user_answer}

Evaluá si la respuesta es correcta (puede ser parcialmente correcta).
Dá un feedback corto, motivador y práctico en español rioplatense.
Incluí un tip concreto que pueda aplicar hoy.

Respondé SOLO en JSON con esta estructura:
{{
  "is_correct": true/false,
  "is_partial": true/false,
  "score": 0-100,
  "feedback": "feedback de 1-2 oraciones, motivador",
  "tip": "tip práctico de 1 oración"
}}"""

    response = await client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    text = response.content[0].text.strip()
    return json.loads(text)


async def generate_onboarding_suggestion(
    answers: list[dict],
    industry: str,
    experience_years: int,
) -> dict:
    """
    Analiza el quiz nivelatorio y sugiere rutas de aprendizaje.
    Retorna: {level, suggested_industries, explanation, quick_win_tip}
    """
    answers_text = "\n".join(
        [f"- {a['question']}: {a['answer']}" for a in answers]
    )

    prompt = f"""Sos un coach de ventas analizando el perfil de un vendedor nuevo.

Industria declarada: {industry}
Años de experiencia: {experience_years}
Respuestas del quiz nivelatorio:
{answers_text}

Determiná su nivel real (beginner/intermediate/advanced) y
qué contenido necesita aprender primero para tener resultados rápidos.

Respondé SOLO en JSON:
{{
  "level": "beginner|intermediate|advanced",
  "strengths": ["fortaleza 1", "fortaleza 2"],
  "gaps": ["área de mejora 1", "área de mejora 2"],
  "priority_topics": ["tema prioritario 1", "tema 2", "tema 3"],
  "explanation": "explicación motivadora de 2-3 oraciones en español rioplatense",
  "quick_win_tip": "una técnica que puede aplicar mañana mismo"
}}"""

    response = await client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    return json.loads(response.content[0].text.strip())


async def generate_module_from_document(
    document_text: str,
    industry: str,
    module_title: str,
    target_level: str = "beginner",
) -> dict:
    """
    Convierte un documento (bibliografía, proceso interno) en un módulo estructurado.
    Este es el feature estrella para las empresas: subís un PDF y sale un curso.
    """
    prompt = f"""Sos un experto en instructional design para ventas.
Tenés el siguiente material sobre {industry}:

---
{document_text[:8000]}
---

Convertí este material en un módulo de capacitación para vendedores de nivel {target_level}.
El módulo se llama: "{module_title}"

Creá exactamente 4 lecciones. Cada lección tiene:
- Una lección de teoría con el concepto clave
- Un quiz de 3 preguntas con opciones múltiples
- Un ejercicio práctico de roleplay

Respondé SOLO en JSON:
{{
  "description": "descripción del módulo en 1-2 oraciones",
  "lessons": [
    {{
      "title": "título de la lección",
      "type": "theory|quiz|roleplay",
      "content": {{
        "text": "contenido principal (para theory)",
        "key_points": ["punto 1", "punto 2"],
        "questions": [  // solo para quiz
          {{
            "question": "pregunta",
            "options": ["A", "B", "C", "D"],
            "correct": 0,
            "explanation": "por qué es correcta"
          }}
        ],
        "scenario": "descripción del roleplay",  // solo para roleplay
        "objective": "qué debe lograr el vendedor"
      }},
      "estimated_minutes": 5,
      "xp_reward": 20
    }}
  ]
}}"""

    response = await client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    text = response.content[0].text.strip()
    # Limpiar posibles backticks de markdown
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


async def coach_chat(
    user_message: str,
    conversation_history: list[dict],
    user_context: dict,
) -> str:
    """
    Chat libre con el coach IA. Responde como coach personalizado
    con contexto del usuario (industria, nivel, progreso reciente).
    """
    system = f"""Sos SalesLeap Coach, un asistente de ventas experto y motivador.
Hablás en español rioplatense, sos directo y práctico.

Perfil del vendedor:
- Nombre: {user_context.get('name', 'vendedor')}
- Industria: {user_context.get('industry', 'ventas')}
- Nivel: {user_context.get('level', 'beginner')}
- XP total: {user_context.get('total_xp', 0)}
- Racha actual: {user_context.get('streak', 0)} días

Tus respuestas son cortas (máx 3 párrafos), accionables y específicas a su industria.
Si pregunta algo que debería aprender en un módulo, sugerís el contenido de SalesLeap."""

    messages = conversation_history + [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system,
        messages=messages,
    )
    return response.content[0].text
