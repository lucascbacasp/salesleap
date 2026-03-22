"""
SalesLeap — AI Coach Service
Motor Claude con restricción de dominio por industry del usuario.
"""
import json
from typing import Optional
import anthropic
from app.core.config import settings
from app.services.changan_knowledge import CHANGAN_KNOWLEDGE

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
MODEL = "claude-3-haiku-20240307"

# ── Configuraciones por industry ──────────────────────────────────────────────
INDUSTRY_COACH_CONFIG = {
    "onboarding_alimentaria": {
        "persona": "Coach de Inocuidad Alimentaria",
        "scope_description": (
            "la capacitación de inocuidad alimentaria del programa Operario Habilitado de Servagrop"
        ),
        "allowed_topics": [
            "Buenas Prácticas de Manufactura (BPM)",
            "estándar BRCGS y requisitos de certificación",
            "Puntos Críticos de Control (CCPs) y HACCP",
            "trazabilidad de productos y materias primas",
            "higiene personal y del entorno de planta",
            "limpieza y desinfección (L+D) de equipos y superficies",
            "gestión de alérgenos (especialmente maní)",
            "módulos del programa Servagrop: Guardián de la inocuidad, Operador de puntos críticos, Operario habilitado",
            "preguntas o ejercicios de los quizzes y roleplays del programa",
            "dudas sobre lecciones o contenidos del path de inocuidad",
        ],
        "out_of_scope_reply": (
            "Esa pregunta está fuera de mi área de conocimiento. "
            "Puedo ayudarte con todo lo relacionado a tu capacitación de inocuidad alimentaria."
        ),
    },
    "alimentaria": {
        "persona": "Coach de Inocuidad Alimentaria",
        "scope_description": "inocuidad alimentaria, BPM, BRCGS y seguridad en planta",
        "allowed_topics": [
            "Buenas Prácticas de Manufactura (BPM)",
            "estándar BRCGS",
            "Puntos Críticos de Control (CCPs) y HACCP",
            "trazabilidad y gestión de alérgenos",
            "higiene y limpieza en planta",
        ],
        "out_of_scope_reply": (
            "Esa pregunta está fuera de mi área de conocimiento. "
            "Puedo ayudarte con todo lo relacionado a inocuidad alimentaria y seguridad en planta."
        ),
    },
    "auto": {
        "persona": "Coach de Ventas Automotrices",
        "scope_description": "técnicas de venta y posventa en concesionarias automotrices",
        "allowed_topics": [
            "técnicas de venta consultiva automotriz",
            "manejo de objeciones de clientes en sala de autos",
            "cierre de ventas y negociación de precio/financiación",
            "posventa y fidelización de clientes automotrices",
            "conocimiento de producto: características, beneficios, test drive",
            "gestión del proceso de entrega del vehículo",
            "métricas de ventas: tasa de cierre, ticket promedio, satisfacción",
            "contenido de los módulos de Venta Consultiva Automotriz",
            "módulo Hablemos de Changan: modelo CS55 Plus PHEV, precios, financiación, objeciones y comparativa",
        ],
        "out_of_scope_reply": (
            "Esa pregunta está fuera de mi área. "
            "Puedo ayudarte con técnicas de venta automotriz, manejo de objeciones y todo lo de tu capacitación."
        ),
        "brand_knowledge": CHANGAN_KNOWLEDGE,
    },
    "inmobiliaria": {
        "persona": "Coach de Ventas Inmobiliarias",
        "scope_description": "técnicas de venta y negociación en el mercado inmobiliario",
        "allowed_topics": [
            "técnicas de venta y captación de propiedades",
            "negociación entre compradores y vendedores",
            "tasación y argumentación de precios de mercado",
            "manejo de objeciones en operaciones inmobiliarias",
            "cierre de escrituras y procesos legales básicos",
            "marketing de propiedades y uso de portales",
            "fidelización y referidos en el negocio inmobiliario",
            "contenido de los módulos de Venta Inmobiliaria",
        ],
        "out_of_scope_reply": (
            "Esa pregunta está fuera de mi área. "
            "Puedo ayudarte con ventas inmobiliarias, captación, negociación y todo lo de tu capacitación."
        ),
    },
}

_DEFAULT_CONFIG = {
    "persona": "SalesLeap Coach",
    "scope_description": "capacitación y desarrollo profesional en ventas",
    "allowed_topics": [
        "técnicas de venta y negociación",
        "manejo de objeciones",
        "comunicación efectiva con clientes",
        "métricas y productividad comercial",
        "contenido de los módulos de capacitación de SalesLeap",
    ],
    "out_of_scope_reply": (
        "Esa pregunta está fuera de mi área. "
        "Puedo ayudarte con todo lo relacionado a tu capacitación en SalesLeap."
    ),
}


def _get_config(industry: Optional[str]) -> dict:
    """Devuelve la config de coach correspondiente al industry del usuario."""
    if not industry:
        return _DEFAULT_CONFIG
    return INDUSTRY_COACH_CONFIG.get(industry, _DEFAULT_CONFIG)


def _build_system_prompt(user_context: dict) -> str:
    """
    Construye el system prompt del coach adaptado al industry del usuario.
    Incluye persona, scope permitido, cláusula de restricción y datos del usuario.
    """
    industry = user_context.get("industry") or ""
    config = _get_config(industry)

    topics_list = "\n".join(f"  - {t}" for t in config["allowed_topics"])

    full_name    = user_context.get("full_name") or user_context.get("name") or "el operario"
    total_xp     = user_context.get("total_xp", 0)
    level        = user_context.get("level", 1)
    streak       = user_context.get("streak_current") or user_context.get("streak", 0)
    current_path = user_context.get("current_path") or "—"
    last_lesson  = user_context.get("last_lesson") or "—"

    brand_block = config.get("brand_knowledge", "")
    brand_section = f"\n\nBASE DE CONOCIMIENTO DE MARCA\n{brand_block}" if brand_block else ""

    return f"""Sos {config['persona']} de SalesLeap.
Hablás en español rioplatense, sos directo, claro y motivador.
Tus respuestas son cortas (máximo 3 párrafos) y siempre accionables.

ALCANCE PERMITIDO
Solo podés responder preguntas relacionadas con {config['scope_description']}.
Los temas que podés tratar son:
{topics_list}

RESTRICCIÓN ESTRICTA
Si el usuario pregunta sobre cualquier tema AJENO a los listados arriba
(economía, política, entretenimiento, tecnología general, o cualquier otra área),
respondé ÚNICAMENTE con este mensaje, sin agregar nada más:
"{config['out_of_scope_reply']}"
No des explicaciones adicionales ni razones. Solo ese mensaje.

PERFIL DEL USUARIO
- Nombre: {full_name}
- XP total: {total_xp}
- Nivel: {level}
- Racha actual: {streak} días
- Path actual: {current_path}
- Última lección: {last_lesson}{brand_section}"""


# ── Funciones públicas ────────────────────────────────────────────────────────

async def coach_chat(
    user_message: str,
    conversation_history: list[dict],
    user_context: dict,
) -> str:
    """
    Chat libre con el coach IA.
    - Limita el historial a los últimos 20 mensajes (10 turnos).
    - Restringe las respuestas al dominio de capacitación del usuario.
    """
    system_prompt = _build_system_prompt(user_context)

    # Limitar historial a últimos 20 mensajes (10 turnos usuario/asistente)
    trimmed_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
    messages = trimmed_history + [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


async def evaluate_answer(
    question: str,
    user_answer: str,
    correct_answer: str,
    user_context: dict,
) -> dict:
    """
    Evalúa la respuesta de un quiz y devuelve feedback personalizado.
    Usa la persona del coach del industry correspondiente.
    Retorna: {is_correct, is_partial, score, feedback, tip}
    """
    industry = user_context.get("industry") or ""
    config = _get_config(industry)
    full_name = user_context.get("full_name") or user_context.get("name") or "el operario"
    level = user_context.get("level", 1)

    prompt = f"""Sos {config['persona']} de SalesLeap evaluando una respuesta de capacitación.

Operario: {full_name} (nivel {level})
Pregunta: {question}
Respuesta correcta: {correct_answer}
Respuesta del operario: {user_answer}

Evaluá si la respuesta es correcta (puede ser parcialmente correcta).
Dá un feedback corto, motivador y práctico en español rioplatense,
contextualizado en {config['scope_description']}.
Incluí un tip concreto que pueda aplicar en su trabajo.

Respondé SOLO en JSON con esta estructura exacta:
{{
  "is_correct": true,
  "is_partial": false,
  "score": 85,
  "feedback": "feedback de 1-2 oraciones, motivador",
  "tip": "tip práctico de 1 oración"
}}"""

    response = await client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    # Limpiar posibles backticks de markdown
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


# ── Funciones legacy (mantenidas para compatibilidad con otros routers) ────────

async def evaluate_quiz_answer(
    question: str,
    user_answer: str,
    correct_answer: str,
    industry: str,
    user_level: str,
) -> dict:
    """Wrapper legacy — usa evaluate_answer internamente."""
    user_context = {"industry": industry, "level": user_level}
    return await evaluate_answer(question, user_answer, correct_answer, user_context)


async def generate_onboarding_suggestion(
    answers: list[dict],
    industry: str,
    experience_years: int,
) -> dict:
    """
    Analiza el quiz nivelatorio y sugiere rutas de aprendizaje.
    Retorna: {level, strengths, gaps, priority_topics, explanation, quick_win_tip}
    """
    answers_text = "\n".join([f"- {a['question']}: {a['answer']}" for a in answers])

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
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.content[0].text.strip())


async def generate_module_from_document(
    document_text: str,
    industry: str,
    module_title: str,
    target_level: str = "beginner",
) -> dict:
    """
    Convierte un documento (bibliografía, proceso interno) en un módulo estructurado.
    """
    prompt = f"""Sos un experto en instructional design para ventas.
Tenés el siguiente material sobre {industry}:

---
{document_text[:8000]}
---

Convertí este material en un módulo de capacitación para vendedores de nivel {target_level}.
El módulo se llama: "{module_title}"

Creá exactamente 4 lecciones con teoría, quiz de 3 preguntas y roleplay.

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
        "questions": [
          {{
            "question": "pregunta",
            "options": ["A", "B", "C", "D"],
            "correct": 0,
            "explanation": "por qué es correcta"
          }}
        ],
        "scenario": "descripción del roleplay",
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
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
