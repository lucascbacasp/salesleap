"""
SalesLeap — Seed Data Script
Populates the database with realistic sales training content.

Usage: python seed.py
"""
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from app.core.database import async_session, engine
from app.models.models import (
    Company, LearningPath, Module, Lesson, User, UserRole, UserPathProgress, ProgressStatus,
)

# ============================================================
# COMPANIES
# ============================================================
COMPANIES = [
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000001"),
        "name": "Toyota Córdoba",
        "slug": "toyota-cba",
        "email_domain": "toyotacba.com.ar",
        "industry": "auto",
        "plan": "pro",
        "is_active": True,
        "settings": {},
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000002"),
        "name": "RE/MAX Córdoba",
        "slug": "remax-cba",
        "email_domain": "remaxcba.com.ar",
        "industry": "inmobiliaria",
        "plan": "pro",
        "is_active": True,
        "settings": {},
    },
]

# ============================================================
# LEARNING PATHS
# ============================================================
AUTO_PATH = {
    "id": uuid.UUID("b0000000-0000-0000-0000-000000000001"),
    "title": "Venta Consultiva Automotriz",
    "description": "Dominá el proceso completo de venta de vehículos: desde la recepción del cliente hasta el cierre y posventa. Aprendé técnicas probadas de los mejores asesores comerciales.",
    "industry": "auto",
    "level": "beginner",
    "company_id": None,
    "xp_reward": 500,
    "order_index": 0,
    "is_published": True,
}

INMOB_PATH = {
    "id": uuid.UUID("b0000000-0000-0000-0000-000000000002"),
    "title": "Cierre Inmobiliario Profesional",
    "description": "Convertite en un asesor inmobiliario de alto rendimiento. Aprendé a captar propiedades, calificar compradores, manejar objeciones de precio y cerrar operaciones complejas.",
    "industry": "inmobiliaria",
    "level": "beginner",
    "company_id": None,
    "xp_reward": 500,
    "order_index": 0,
    "is_published": True,
}

# ============================================================
# MODULES & LESSONS — AUTOMOTRIZ
# ============================================================
AUTO_MODULES = [
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000001"),
        "path_id": AUTO_PATH["id"],
        "title": "Recepción y Detección de Necesidades",
        "description": "Cómo generar una primera impresión impecable y descubrir qué busca realmente el cliente.",
        "order_index": 0,
        "xp_reward": 100,
        "estimated_minutes": 25,
        "is_published": True,
        "lessons": [
            {
                "title": "Los primeros 30 segundos: el saludo que vende",
                "lesson_type": "theory",
                "order_index": 0,
                "xp_reward": 20,
                "estimated_minutes": 5,
                "content": {
                    "text": "En la venta automotriz, los primeros 30 segundos definen el 80% de la experiencia del cliente. Un saludo profesional, cálido y sin presión genera confianza inmediata.\n\nEl cliente que entra a un concesionario ya tomó una decisión importante: salió de su casa para ver autos. Tu trabajo no es 'venderle', sino ayudarlo a tomar la mejor decisión.",
                    "key_points": [
                        "Saludá con contacto visual y sonrisa genuina antes de que el cliente llegue al mostrador",
                        "Presentate con nombre y rol: 'Soy Lucas, asesor comercial. ¿En qué puedo ayudarte?'",
                        "Nunca preguntes '¿Qué auto buscás?' como primera pregunta — es demasiado directa",
                        "Usá preguntas abiertas: '¿Es tu primera visita?' o '¿Venís con alguna idea en mente?'",
                        "Dale espacio: 'Si querés recorrer tranquilo, estoy por acá cuando me necesites'"
                    ],
                    "summary": "El saludo ideal es cálido, profesional y sin presión. Presentate, hacé una pregunta abierta y respetá el espacio del cliente."
                },
            },
            {
                "title": "Preguntas de descubrimiento: el método SPIN",
                "lesson_type": "quiz",
                "order_index": 1,
                "xp_reward": 25,
                "estimated_minutes": 7,
                "content": {
                    "text": "El método SPIN (Situación, Problema, Implicación, Necesidad) te ayuda a entender qué necesita realmente el cliente sin sonar como un interrogatorio.",
                    "questions": [
                        {
                            "question": "Un cliente dice 'Estoy viendo opciones'. ¿Cuál es la mejor pregunta SPIN de Situación?",
                            "options": [
                                "¿Cuánto querés gastar?",
                                "¿Qué vehículo tenés actualmente y cómo lo usás en el día a día?",
                                "¿Te interesa un SUV o un sedán?",
                                "¿Ya viste precios en otros concesionarios?"
                            ],
                            "correct": 1,
                            "explanation": "Las preguntas de Situación buscan entender el contexto actual del cliente sin presionar. Saber qué tiene hoy y cómo lo usa te da información valiosa para recomendar."
                        },
                        {
                            "question": "¿Cuál es una buena pregunta SPIN de Problema?",
                            "options": [
                                "¿Tu auto actual tiene algún problema mecánico?",
                                "¿Hay algo de tu vehículo actual que ya no se adapte a tu vida?",
                                "¿Tu auto es viejo?",
                                "¿No te gusta tu auto?"
                            ],
                            "correct": 1,
                            "explanation": "Las preguntas de Problema exploran insatisfacciones sin ser negativas. 'Algo que ya no se adapte' es neutral y abre la conversación."
                        },
                        {
                            "question": "Un cliente dice que su auto le queda chico para la familia. ¿Qué pregunta de Implicación usarías?",
                            "options": [
                                "Entonces necesitás una SUV",
                                "¿Y eso cómo afecta los viajes del fin de semana con tu familia?",
                                "Te muestro la Hilux que es más grande",
                                "¿Cuántos hijos tenés?"
                            ],
                            "correct": 1,
                            "explanation": "Las preguntas de Implicación hacen que el cliente sienta el peso del problema. Al conectar con situaciones concretas (viajes familiares), el cliente se motiva a buscar una solución."
                        }
                    ],
                },
            },
            {
                "title": "Roleplay: Recibí a un cliente que llega sin turno",
                "lesson_type": "roleplay",
                "order_index": 2,
                "xp_reward": 30,
                "estimated_minutes": 8,
                "content": {
                    "scenario": "Es sábado a la mañana. Un hombre de unos 35 años entra al concesionario mirando para todos lados. No tiene turno. Se lo nota un poco incómodo. Se acerca a un Corolla Cross que está en exhibición y empieza a mirar el precio en el cartel.\n\nTu objetivo es hacer un saludo profesional, generar rapport y hacer al menos 2 preguntas de descubrimiento sin que se sienta presionado.",
                    "objective": "Demostrá que podés recibir a un cliente sin turno de forma natural, generando confianza y descubriendo sus necesidades.",
                    "evaluation_criteria": [
                        "Saludo cálido y profesional",
                        "No empezar hablando del auto directamente",
                        "Hacer preguntas abiertas de descubrimiento",
                        "Respetar el espacio del cliente"
                    ],
                },
            },
            {
                "title": "Desafío: Identificá el tipo de comprador",
                "lesson_type": "challenge",
                "order_index": 3,
                "xp_reward": 35,
                "estimated_minutes": 5,
                "content": {
                    "text": "Cada cliente tiene un perfil de compra diferente. Identificar el tipo te permite adaptar tu comunicación.",
                    "questions": [
                        {
                            "question": "Un cliente llega con una planilla comparando 3 modelos, precios y consumos. ¿Qué tipo de comprador es?",
                            "options": [
                                "Emocional — se deja llevar por el diseño",
                                "Analítico — necesita datos y comparaciones",
                                "Impulsivo — quiere comprar ya",
                                "Social — le importa qué opinan los demás"
                            ],
                            "correct": 1,
                            "explanation": "El comprador analítico investiga antes de visitar. Necesita datos, fichas técnicas y tiempo para decidir. No lo presiones — dale información de calidad."
                        },
                        {
                            "question": "Una clienta dice 'Mi vecina se compró uno igual y le encanta'. ¿Qué tipo de compradora es?",
                            "options": [
                                "Analítica",
                                "Impulsiva",
                                "Social — valida con su entorno",
                                "Emocional"
                            ],
                            "correct": 2,
                            "explanation": "El comprador social busca validación externa. Mencioná testimonios, cantidad vendida y opiniones de otros clientes para reforzar su decisión."
                        }
                    ],
                },
            },
        ],
    },
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000002"),
        "path_id": AUTO_PATH["id"],
        "title": "Presentación y Test Drive",
        "description": "Convertí una presentación de producto en una experiencia memorable que conecte con las emociones del cliente.",
        "order_index": 1,
        "xp_reward": 100,
        "estimated_minutes": 25,
        "is_published": True,
        "lessons": [
            {
                "title": "La presentación CPB: Característica → Puente → Beneficio",
                "lesson_type": "theory",
                "order_index": 0,
                "xp_reward": 20,
                "estimated_minutes": 5,
                "content": {
                    "text": "El error más común del vendedor automotriz es listar características técnicas. Al cliente no le importa que el motor tenga 170 CV — le importa que pueda pasar camiones en ruta con seguridad.\n\nEl método CPB transforma cada característica en un beneficio concreto para ESE cliente.",
                    "key_points": [
                        "Característica: dato técnico ('tiene 7 airbags')",
                        "Puente: la conexión ('lo que significa para vos es que...')",
                        "Beneficio: impacto emocional ('tu familia viaja protegida')",
                        "Siempre personalizá el beneficio según lo que descubriste en la entrevista",
                        "Ejemplo: 'Este motor tiene Start/Stop (C), eso significa que en el tráfico de Córdoba (P), vas a ahorrar hasta un 15% de combustible por mes (B)'"
                    ],
                    "summary": "Nunca vendas características — vendé beneficios personalizados usando el puente emocional."
                },
            },
            {
                "title": "Quiz: Convertí características en beneficios",
                "lesson_type": "quiz",
                "order_index": 1,
                "xp_reward": 25,
                "estimated_minutes": 7,
                "content": {
                    "text": "Practicá el método CPB identificando el mejor beneficio para cada situación.",
                    "questions": [
                        {
                            "question": "El cliente es padre de 3 hijos. ¿Cómo presentás el baúl de 440 litros?",
                            "options": [
                                "El baúl tiene 440 litros de capacidad",
                                "Es el baúl más grande del segmento",
                                "Con 440 litros, te entra todo para las vacaciones en familia sin tener que elegir qué dejar",
                                "Podés meter muchas cosas"
                            ],
                            "correct": 2,
                            "explanation": "Perfecto CPB: la característica (440L) conectada con su realidad (familia, vacaciones) genera un beneficio emocional concreto."
                        },
                        {
                            "question": "La clienta trabaja en ventas y hace muchos kilómetros. ¿Cómo presentás el consumo de 5.2L/100km?",
                            "options": [
                                "Consume 5.2 litros cada 100 km",
                                "Es muy económico",
                                "Con ese consumo, en tus 2000 km mensuales te ahorrás más de $50.000 en nafta comparado con tu auto actual",
                                "Gasta poco"
                            ],
                            "correct": 2,
                            "explanation": "Excelente: tradujiste un número técnico en un ahorro mensual concreto y relevante para su situación laboral."
                        },
                        {
                            "question": "¿Cuál es el mejor momento para hacer el test drive?",
                            "options": [
                                "Al principio, antes de hablar de precios",
                                "Después de descubrir necesidades y presentar beneficios relevantes",
                                "Solo si el cliente lo pide",
                                "Al final, después de negociar el precio"
                            ],
                            "correct": 1,
                            "explanation": "El test drive tiene más impacto cuando el cliente ya entendió los beneficios. Así la experiencia confirma lo que le contaste y genera el 'quiero este'."
                        }
                    ],
                },
            },
            {
                "title": "Roleplay: Presentá un vehículo a una familia",
                "lesson_type": "roleplay",
                "order_index": 2,
                "xp_reward": 30,
                "estimated_minutes": 8,
                "content": {
                    "scenario": "Una pareja joven (30 años) con un bebé de 6 meses llega al concesionario. Quieren cambiar su Gol Trend por algo más seguro y espacioso. El presupuesto es ajustado. Están mirando un Corolla Cross.\n\nPresentá al menos 3 características del vehículo usando el método CPB, personalizadas para esta familia.",
                    "objective": "Demostrá dominio del método CPB adaptando la presentación a las necesidades específicas de una familia joven.",
                    "evaluation_criteria": [
                        "Usa el método CPB correctamente",
                        "Personaliza beneficios para una familia con bebé",
                        "Menciona seguridad, espacio y economía",
                        "No habla de precio a menos que el cliente lo pida"
                    ],
                },
            },
            {
                "title": "Desafío: El test drive perfecto",
                "lesson_type": "challenge",
                "order_index": 3,
                "xp_reward": 35,
                "estimated_minutes": 5,
                "content": {
                    "text": "El test drive es la herramienta de cierre más poderosa en ventas automotrices. Un test drive bien conducido aumenta la tasa de cierre en un 40%.",
                    "questions": [
                        {
                            "question": "¿Qué deberías hacer ANTES de que el cliente suba al auto?",
                            "options": [
                                "Darle las llaves y dejarlo ir solo",
                                "Ajustar asiento, espejos, y explicar los controles principales mientras está sentado",
                                "Hablarle de las promociones actuales",
                                "Pedirle que firme papeles"
                            ],
                            "correct": 1,
                            "explanation": "Preparar el auto muestra profesionalismo y le da seguridad al cliente. Es un ritual que genera confianza."
                        },
                        {
                            "question": "Durante el test drive, el cliente dice 'qué suave va'. ¿Qué hacés?",
                            "options": [
                                "Decís 'sí, es muy bueno'",
                                "Anclás la emoción: '¿Te imaginás yendo así todos los días al trabajo? Ese confort es tuyo cada mañana'",
                                "Le hablás del motor y la transmisión",
                                "Le preguntás si quiere ver otro modelo"
                            ],
                            "correct": 1,
                            "explanation": "Cuando el cliente expresa una emoción positiva, anclala a su vida cotidiana. Eso transforma una sensación en una necesidad."
                        }
                    ],
                },
            },
        ],
    },
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000003"),
        "path_id": AUTO_PATH["id"],
        "title": "Manejo de Objeciones y Cierre",
        "description": "Las objeciones no son rechazo — son señales de interés. Aprendé a transformarlas en oportunidades de cierre.",
        "order_index": 2,
        "xp_reward": 150,
        "estimated_minutes": 30,
        "is_published": True,
        "lessons": [
            {
                "title": "Las 5 objeciones más comunes y cómo responder",
                "lesson_type": "theory",
                "order_index": 0,
                "xp_reward": 20,
                "estimated_minutes": 6,
                "content": {
                    "text": "El 90% de las objeciones en venta automotriz caen en 5 categorías. Si preparás respuestas para estas, vas a manejar el 90% de las situaciones.\n\nLa clave: nunca discutas una objeción. Validá la preocupación, preguntá para entender y redirigí hacia el valor.",
                    "key_points": [
                        "'Es muy caro' → No discutas el precio. Preguntá: '¿Comparado con qué?' y mostrá el costo total de propiedad (mantenimiento, consumo, reventa)",
                        "'Lo tengo que pensar' → Respetá, pero preguntá: '¿Qué información te ayudaría a decidir?' o '¿Hay algo que no cubrimos?'",
                        "'Vi algo más barato' → 'Entiendo. ¿Comparaste las mismas especificaciones? Te armo una comparación punto por punto'",
                        "'Mi pareja tiene que verlo' → '¡Perfecto! ¿Querés que agendemos una visita juntos? Le preparo todo para que aproveche el tiempo'",
                        "'No es el momento' → '¿Qué cambiaría en los próximos meses? Porque los precios suelen ajustarse y tu usado vale más hoy que mañana'"
                    ],
                    "summary": "Validá → Preguntá → Redirigí. Nunca discutas ni presiones."
                },
            },
            {
                "title": "Quiz: ¿Cómo respondés a cada objeción?",
                "lesson_type": "quiz",
                "order_index": 1,
                "xp_reward": 25,
                "estimated_minutes": 7,
                "content": {
                    "text": "Poné a prueba tu capacidad de manejar objeciones reales.",
                    "questions": [
                        {
                            "question": "El cliente dice: 'Me encanta pero es $2 millones más que el de la competencia'. ¿Mejor respuesta?",
                            "options": [
                                "Le ofrezco un descuento inmediatamente",
                                "Le digo que nuestro auto es mejor",
                                "'Entiendo la diferencia. ¿Querés que comparemos qué incluye cada uno? Muchas veces la diferencia se paga sola en reventa y mantenimiento'",
                                "Le digo que el de la competencia es malo"
                            ],
                            "correct": 2,
                            "explanation": "Validás su preocupación, no bajás el precio, y redirigís a una comparación objetiva donde podés mostrar valor real."
                        },
                        {
                            "question": "Después de un test drive excelente, el cliente dice 'Lo pienso y te llamo'. ¿Qué hacés?",
                            "options": [
                                "Le decís 'dale, te espero'",
                                "'Perfecto. ¿Te parece si te mando un resumen por mail con los números? Y si querés, agendamos una llamada el jueves para resolver cualquier duda'",
                                "Le decís que la oferta vence mañana",
                                "Le pedís el número de teléfono de su pareja"
                            ],
                            "correct": 1,
                            "explanation": "Siempre dejá un siguiente paso concreto. Un mail con números y una llamada agendada mantienen viva la oportunidad sin presionar."
                        },
                        {
                            "question": "¿Cuál es la técnica de cierre más efectiva en ventas automotrices?",
                            "options": [
                                "El cierre por presión: 'Si no comprás hoy, se lo lleva otro'",
                                "El cierre alternativo: '¿Lo preferís en blanco o gris?'",
                                "El cierre por resumen: revisás los beneficios acordados y preguntás '¿Avanzamos con la reserva?'",
                                "Ofrecer el mejor descuento posible"
                            ],
                            "correct": 2,
                            "explanation": "El cierre por resumen es el más profesional: repasás lo que el cliente valoró, confirmás que cubre sus necesidades, y proponés el siguiente paso natural."
                        }
                    ],
                },
            },
            {
                "title": "Roleplay: Cerrá la venta de una Hilux",
                "lesson_type": "roleplay",
                "order_index": 2,
                "xp_reward": 35,
                "estimated_minutes": 10,
                "content": {
                    "scenario": "Martín (45 años, empresario agropecuario) hizo un test drive de la Hilux SRX hace 3 días. Vuelve hoy con su señora. Le encantó el auto pero dice que el precio es alto y que en otra concesionaria le ofrecieron $500.000 menos por un modelo similar.\n\nTu objetivo es manejar la objeción de precio, presentar el valor diferencial, e intentar cerrar la venta hoy.",
                    "objective": "Demostrá que podés manejar una objeción de precio de un cliente informado y avanzar hacia el cierre sin recurrir a descuentos innecesarios.",
                    "evaluation_criteria": [
                        "Valida la objeción sin ponerse a la defensiva",
                        "Compara valor, no solo precio",
                        "Involucra a la pareja en la conversación",
                        "Usa cierre por resumen o alternativo",
                        "No ofrece descuento como primera opción"
                    ],
                },
            },
            {
                "title": "Desafío final: Cierre bajo presión",
                "lesson_type": "challenge",
                "order_index": 3,
                "xp_reward": 40,
                "estimated_minutes": 7,
                "content": {
                    "text": "Situaciones de cierre complejas que requieren pensamiento rápido y técnica avanzada.",
                    "questions": [
                        {
                            "question": "El cliente está listo para firmar pero pide un 10% de descuento que no podés dar. ¿Qué hacés?",
                            "options": [
                                "Le decís que no podés y listo",
                                "Le ofrecés valor agregado: accesorios, service gratis, seguro bonificado — cosas que cuestan menos que el 10% pero el cliente percibe como valiosas",
                                "Consultás al gerente para ver si se puede",
                                "Le bajás el precio del usado que entrega"
                            ],
                            "correct": 1,
                            "explanation": "Agregar valor en lugar de bajar precio protege tu margen y satisface al cliente. Los accesorios y servicios tienen alto valor percibido y bajo costo real."
                        },
                        {
                            "question": "El cliente dice 'Voy a esperar al modelo nuevo que sale en 3 meses'. ¿Mejor respuesta?",
                            "options": [
                                "Le decís que el modelo nuevo va a ser más caro",
                                "'Entiendo. El modelo nuevo va a tener cambios estéticos, pero las bondades mecánicas son las mismas. Además, comprando hoy tenés la ventaja de precio actual + entrega inmediata. ¿Querés que hagamos los números con tu usado?'",
                                "Le pedís que vuelva en 3 meses",
                                "Le decís que no va a haber stock del nuevo"
                            ],
                            "correct": 1,
                            "explanation": "Información honesta + ventaja concreta de comprar hoy (precio + entrega) + avance hacia los números. Es urgencia legítima, no presión falsa."
                        }
                    ],
                },
            },
        ],
    },
]

# ============================================================
# MODULES & LESSONS — INMOBILIARIA
# ============================================================
INMOB_MODULES = [
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000004"),
        "path_id": INMOB_PATH["id"],
        "title": "Captación de Propiedades",
        "description": "El negocio inmobiliario empieza por la captación. Aprendé a conseguir propiedades exclusivas y a generar confianza con los propietarios.",
        "order_index": 0,
        "xp_reward": 100,
        "estimated_minutes": 25,
        "is_published": True,
        "lessons": [
            {
                "title": "El speech de captación que convence al propietario",
                "lesson_type": "theory",
                "order_index": 0,
                "xp_reward": 20,
                "estimated_minutes": 6,
                "content": {
                    "text": "El propietario tiene miedo. Miedo a que le cobren de más, a que no le vendan, a que le hagan perder tiempo. Tu trabajo en la captación es eliminar esos miedos con transparencia y profesionalismo.\n\nEl speech de captación no es un discurso de venta — es una conversación donde demostrás que entendés el mercado, tenés un plan y podés vender su propiedad más rápido que él solo.",
                    "key_points": [
                        "Empezá preguntando: '¿Por qué decidiste vender?' — la razón define la urgencia y la estrategia",
                        "Mostrá datos de mercado: propiedades similares, precios por m², tiempo promedio de venta en la zona",
                        "Explicá tu plan de comercialización: fotos profesionales, portales, redes, cartelería, open house",
                        "Sé transparente con la comisión: '3% + IVA es la inversión. Si no vendo, no cobrás nada'",
                        "Pedí exclusiva con argumento: 'Con exclusiva puedo invertir más en marketing porque sé que voy a recuperar la inversión'"
                    ],
                    "summary": "La captación se gana con datos, plan concreto y transparencia. El propietario necesita confiar en que sos profesional."
                },
            },
            {
                "title": "Quiz: Errores comunes en captación",
                "lesson_type": "quiz",
                "order_index": 1,
                "xp_reward": 25,
                "estimated_minutes": 7,
                "content": {
                    "text": "Evitá los errores que te hacen perder captaciones.",
                    "questions": [
                        {
                            "question": "Un propietario quiere publicar a $120.000 USD pero el mercado dice que vale $95.000. ¿Qué hacés?",
                            "options": [
                                "Aceptás el precio para no perder la captación",
                                "Le decís directamente que está equivocado",
                                "Le mostrás comparables vendidos en la zona y le explicás: 'A $120k vamos a tener visitas pero no ofertas. Te propongo arrancar a $99k y generar urgencia'",
                                "Le decís que probás un mes a su precio y después bajás"
                            ],
                            "correct": 2,
                            "explanation": "Los datos matan las emociones. Con comparables reales, el propietario entiende. Proponer un precio competitivo con estrategia muestra profesionalismo."
                        },
                        {
                            "question": "¿Cuándo es el mejor momento para pedir la exclusiva?",
                            "options": [
                                "En la primera llamada",
                                "Después de la tasación, cuando demostraste tu análisis de mercado y plan de comercialización",
                                "Nunca, la exclusiva espanta clientes",
                                "Solo si la propiedad es cara"
                            ],
                            "correct": 1,
                            "explanation": "La exclusiva se pide cuando ya demostraste valor. Después de la tasación, el propietario vio tus datos, tu plan y tu profesionalismo."
                        },
                        {
                            "question": "Un propietario dice 'Tengo otro corredor que me cobra 2%'. ¿Qué respondés?",
                            "options": [
                                "Igualo la comisión al 2%",
                                "'Entiendo. La diferencia entre 2% y 3% en tu propiedad son $X. Eso es lo que invierto en fotos profesionales, drone, staging virtual y publicidad premium. ¿El otro corredor incluye todo eso?'",
                                "Le digo que el otro es poco profesional",
                                "Le digo que es innegociable"
                            ],
                            "correct": 1,
                            "explanation": "Tradujiste la diferencia de comisión en servicios concretos que el otro no ofrece. Nunca bajes la comisión — justificala."
                        }
                    ],
                },
            },
            {
                "title": "Roleplay: Captá un departamento en Nueva Córdoba",
                "lesson_type": "roleplay",
                "order_index": 2,
                "xp_reward": 30,
                "estimated_minutes": 8,
                "content": {
                    "scenario": "Silvia (55 años) heredó un departamento de 2 ambientes en Nueva Córdoba. Quiere venderlo pero no tiene urgencia. Ya habló con otro corredor que le dijo que vale $85.000 USD. Ella cree que vale más porque 'la zona subió mucho'.\n\nTu objetivo es hacer una captación profesional: tasá la propiedad con datos reales, manejá la expectativa de precio y pedí la exclusiva.",
                    "objective": "Demostrá que podés captar una propiedad manejando expectativas de precio con datos y profesionalismo.",
                    "evaluation_criteria": [
                        "Pregunta la razón de venta y urgencia",
                        "Usa datos comparables para justificar el precio",
                        "No acepta un precio irreal solo por captar",
                        "Explica el plan de comercialización",
                        "Pide exclusiva con argumentos"
                    ],
                },
            },
            {
                "title": "Desafío: Tasación rápida",
                "lesson_type": "challenge",
                "order_index": 3,
                "xp_reward": 35,
                "estimated_minutes": 5,
                "content": {
                    "text": "La tasación es tu herramienta de credibilidad. Evaluá estas situaciones.",
                    "questions": [
                        {
                            "question": "Un dpto de 45m² en Nueva Córdoba, 10 años de antigüedad, sin cochera. Comparables vendidos: $1.800-2.000 USD/m². ¿Cuál es el rango justo?",
                            "options": [
                                "$90.000 - $100.000 USD",
                                "$81.000 - $90.000 USD",
                                "$70.000 - $80.000 USD",
                                "$100.000 - $110.000 USD"
                            ],
                            "correct": 1,
                            "explanation": "$1.800 x 45 = $81.000 y $2.000 x 45 = $90.000. Sin cochera no podés estar arriba del rango. $81k-$90k es lo justo."
                        },
                        {
                            "question": "¿Qué factor reduce MÁS el valor de una propiedad en el mercado actual?",
                            "options": [
                                "Que sea PB sin balcón",
                                "Que no tenga cochera propia",
                                "Que tenga más de 20 años",
                                "Que esté en un 3er piso sin ascensor"
                            ],
                            "correct": 1,
                            "explanation": "En el mercado actual de Córdoba, la cochera es el factor que más impacta el precio. Un dpto sin cochera puede valer 10-15% menos."
                        }
                    ],
                },
            },
        ],
    },
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000005"),
        "path_id": INMOB_PATH["id"],
        "title": "Calificación de Compradores",
        "description": "No todos los interesados son compradores reales. Aprendé a calificar rápido para enfocar tu tiempo en los que van a cerrar.",
        "order_index": 1,
        "xp_reward": 100,
        "estimated_minutes": 25,
        "is_published": True,
        "lessons": [
            {
                "title": "El método BANT para inmobiliaria",
                "lesson_type": "theory",
                "order_index": 0,
                "xp_reward": 20,
                "estimated_minutes": 5,
                "content": {
                    "text": "El 70% de las consultas inmobiliarias no se convierten en operación. La diferencia entre un asesor que cierra 2 operaciones por mes y uno que cierra 6 es la calificación.\n\nEl método BANT adaptado a inmobiliaria te permite filtrar en los primeros 5 minutos.",
                    "key_points": [
                        "B (Budget/Presupuesto): '¿Tenés definido un rango de inversión?' — Si no tiene presupuesto claro, no es comprador aún",
                        "A (Authority/Autoridad): '¿La decisión la tomás solo/a o con alguien más?' — Siempre necesitás a todos los decisores en la visita",
                        "N (Need/Necesidad): '¿Qué buscás? ¿Para vivir, invertir o alquilar?' — Define qué propiedades mostrar",
                        "T (Timeline/Tiempo): '¿Para cuándo necesitás mudarte?' — Urgencia = prioridad alta en tu agenda",
                        "Si tiene los 4 elementos, es un prospecto A. Si le faltan 2 o más, es un C que todavía no está listo."
                    ],
                    "summary": "Calificá en los primeros 5 minutos con BANT. Enfocá tu energía en prospectos A con presupuesto, autoridad, necesidad y urgencia."
                },
            },
            {
                "title": "Quiz: ¿Prospecto A, B o C?",
                "lesson_type": "quiz",
                "order_index": 1,
                "xp_reward": 25,
                "estimated_minutes": 7,
                "content": {
                    "text": "Clasificá estos prospectos según el método BANT.",
                    "questions": [
                        {
                            "question": "Llama Juan: 'Busco 2 ambientes hasta USD 70k, para mi hijo que empieza la facultad en marzo. Ya tengo la plata'.",
                            "options": [
                                "Prospecto C — está averiguando",
                                "Prospecto B — le falta definir zona",
                                "Prospecto A — tiene presupuesto, necesidad, timeline y probablemente autoridad",
                                "Prospecto B — no sabemos si decide solo"
                            ],
                            "correct": 2,
                            "explanation": "Budget: $70k definido. Need: para su hijo, universidad. Timeline: marzo (urgente). Authority: es padre, decide. Prospecto A clarísimo — priorizalo."
                        },
                        {
                            "question": "Consulta por Instagram: 'Hola, ¿cuánto sale un dpto en Nueva Córdoba? Es para ver opciones a futuro'.",
                            "options": [
                                "Prospecto A — muestra interés",
                                "Prospecto C — no tiene presupuesto, necesidad difusa, sin timeline",
                                "Prospecto B — hay que nutrirlo",
                                "No vale la pena responder"
                            ],
                            "correct": 1,
                            "explanation": "Sin presupuesto definido, sin timeline, necesidad vaga. Es un C. Respondé amable, mandalo al sitio web y ponelo en un nurturing automático."
                        },
                        {
                            "question": "Te llama María: 'Mi marido y yo vendimos nuestra casa y buscamos algo más chico en zona norte. Tenemos $120k. ¿Podemos ver opciones esta semana?'",
                            "options": [
                                "Prospecto B",
                                "Prospecto C",
                                "Prospecto A — todos los criterios BANT presentes",
                                "Prospecto A pero hay que verificar si el marido está de acuerdo"
                            ],
                            "correct": 2,
                            "explanation": "Budget: $120k. Authority: ella y marido (ambos decisores involucrados). Need: achicarse, zona definida. Timeline: 'esta semana'. Prospecto A perfecto."
                        }
                    ],
                },
            },
            {
                "title": "Roleplay: Calificá una consulta telefónica",
                "lesson_type": "roleplay",
                "order_index": 2,
                "xp_reward": 30,
                "estimated_minutes": 8,
                "content": {
                    "scenario": "Recibís una llamada de Pablo. Dice que vio un departamento tuyo publicado en Zonaprop y quiere visitarlo. No sabés nada más de él.\n\nTu objetivo es calificarlo con BANT en menos de 5 minutos de conversación natural, sin que se sienta interrogado. Tenés que determinar si es un prospecto A, B o C.",
                    "objective": "Demostrá que podés calificar un prospecto telefónico de forma natural y eficiente usando BANT.",
                    "evaluation_criteria": [
                        "Hace las 4 preguntas BANT de forma conversacional",
                        "No suena como un interrogatorio",
                        "Clasifica correctamente al prospecto",
                        "Propone siguiente paso acorde a la clasificación"
                    ],
                },
            },
            {
                "title": "Desafío: Gestión de agenda inmobiliaria",
                "lesson_type": "challenge",
                "order_index": 3,
                "xp_reward": 35,
                "estimated_minutes": 5,
                "content": {
                    "text": "La gestión del tiempo es crucial. Tu agenda debe priorizar prospectos A.",
                    "questions": [
                        {
                            "question": "Tenés 3 visitas para mañana y llama un prospecto A pidiendo ver una propiedad. Tu agenda está llena. ¿Qué hacés?",
                            "options": [
                                "Le decís que no tenés lugar y le ofrecés otro día",
                                "Revisás tus 3 visitas: si alguna es un prospecto B o C, la reprogramás para hacer lugar al A",
                                "Le pedís a un colega que lo atienda",
                                "Le mandás fotos y videos para que decida sin visitar"
                            ],
                            "correct": 1,
                            "explanation": "Los prospectos A siempre tienen prioridad. Reprogramar un B o C para atender un A es gestión inteligente del tiempo."
                        },
                        {
                            "question": "¿Cuántas propiedades deberías mostrar en la primera visita a un prospecto A?",
                            "options": [
                                "1 sola — la que más se ajusta",
                                "3 como máximo — la ideal, una inferior y una superior",
                                "Todas las que puedas — así ve que tenés variedad",
                                "5 o más — así elige"
                            ],
                            "correct": 1,
                            "explanation": "3 es el número mágico: una que supere el presupuesto (aspiracional), la ideal, y una inferior (para que valore la del medio). Más de 3 genera confusión."
                        }
                    ],
                },
            },
        ],
    },
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000006"),
        "path_id": INMOB_PATH["id"],
        "title": "Negociación y Cierre de Operaciones",
        "description": "El momento de la verdad: cómo llevar una oferta a cierre exitoso manejando las emociones de comprador y vendedor.",
        "order_index": 2,
        "xp_reward": 150,
        "estimated_minutes": 30,
        "is_published": True,
        "lessons": [
            {
                "title": "Anatomía de una negociación inmobiliaria",
                "lesson_type": "theory",
                "order_index": 0,
                "xp_reward": 20,
                "estimated_minutes": 6,
                "content": {
                    "text": "La negociación inmobiliaria es un triángulo: comprador, vendedor y vos en el medio. Tu rol no es 'vender' — es facilitar un acuerdo donde ambas partes sientan que ganaron.\n\nLa mayoría de las operaciones se caen en la negociación por errores del asesor, no por diferencia de precio.",
                    "key_points": [
                        "Nunca transmitas una oferta con opinión: 'Recibí una oferta de $X. ¿Querés que la analicemos?' — dejá que el propietario procese",
                        "Preparate para la contra-oferta: siempre hay al menos 2 rondas. Pedile al comprador que deje margen",
                        "Usá el tiempo a tu favor: '¿Te parece que respondemos mañana a primera hora?' genera urgencia sin presión",
                        "Ancla con datos: 'Las propiedades similares se vendieron a $X en los últimos 60 días' legitima la oferta",
                        "El cierre no es un momento — es un proceso. Desde la primera visita estás cerrando"
                    ],
                    "summary": "Sos facilitador, no vendedor. Transmití ofertas sin opinión, usá datos para anclar y manejá los tiempos estratégicamente."
                },
            },
            {
                "title": "Quiz: Escenarios de negociación",
                "lesson_type": "quiz",
                "order_index": 1,
                "xp_reward": 25,
                "estimated_minutes": 7,
                "content": {
                    "text": "Resolvé estas situaciones reales de negociación.",
                    "questions": [
                        {
                            "question": "El comprador ofrece $80k por una propiedad publicada a $95k. El vendedor te dice 'Es una falta de respeto, no acepto'. ¿Qué hacés?",
                            "options": [
                                "Le decís al comprador que suba la oferta",
                                "Validás al vendedor: 'Entiendo que te parezca baja. ¿Cuál sería el mínimo que aceptarías para poder responder con una contra-oferta?'",
                                "Rechazás la oferta sin contraoferta",
                                "Le decís al vendedor que el mercado está difícil"
                            ],
                            "correct": 1,
                            "explanation": "Validás la emoción del vendedor y redirigís a un número concreto. Siempre buscá que haya contraoferta — una negociación muerta no genera comisión."
                        },
                        {
                            "question": "La negociación está trabada en $85k (comprador) vs $90k (vendedor). $5k de diferencia. ¿Cómo destrabás?",
                            "options": [
                                "Le pedís a cada uno que ceda $2.500",
                                "Proponés partir la diferencia",
                                "Buscás variables creativas: plazo de entrega, inclusión de muebles, condiciones de pago — algo que tenga valor para uno sin costar mucho al otro",
                                "Esperás a que alguno ceda"
                            ],
                            "correct": 2,
                            "explanation": "Las variables creativas destraban negociaciones. Quizás el comprador acepta $90k si incluye el aire acondicionado y los muebles del living, que al vendedor no le sirven."
                        },
                        {
                            "question": "Cerraste la negociación verbal a $88k. ¿Cuál es tu siguiente paso?",
                            "options": [
                                "Celebrás y esperás a que se comuniquen para la seña",
                                "Agendás la firma de la reserva para las próximas 24-48hs, con instrucciones claras: monto de seña, escribanía, documentación necesaria",
                                "Le mandás un WhatsApp diciendo 'felicitaciones'",
                                "Esperás al lunes para hacer los papeles"
                            ],
                            "correct": 1,
                            "explanation": "El acuerdo verbal no vale nada. Mové rápido a la reserva/seña. Cada hora que pasa, aumenta el riesgo de que alguien se arrepienta."
                        }
                    ],
                },
            },
            {
                "title": "Roleplay: Negociá una contraoferta",
                "lesson_type": "roleplay",
                "order_index": 2,
                "xp_reward": 35,
                "estimated_minutes": 10,
                "content": {
                    "scenario": "Tenés una propiedad captada a $95.000 USD en Cerro de las Rosas. Llegó una oferta de $82.000. El vendedor (Roberto, jubilado) necesita vender para mudarse a Buenos Aires con su hija, pero no quiere 'regalar' su casa.\n\nTenés que llamar a Roberto, transmitirle la oferta profesionalmente, manejar su reacción emocional, y obtener una contraoferta razonable para mantener viva la negociación.",
                    "objective": "Demostrá que podés transmitir una oferta baja a un vendedor emocional, validar sus sentimientos y obtener una contraoferta que mantenga la negociación activa.",
                    "evaluation_criteria": [
                        "Transmite la oferta sin opinión personal",
                        "Valida la emoción del vendedor",
                        "Usa datos de mercado para contextualizar",
                        "Obtiene una contraoferta concreta",
                        "Mantiene la relación de confianza"
                    ],
                },
            },
            {
                "title": "Desafío final: De la reserva al cierre",
                "lesson_type": "challenge",
                "order_index": 3,
                "xp_reward": 40,
                "estimated_minutes": 7,
                "content": {
                    "text": "Los últimos pasos antes de la escritura son críticos. Un error acá puede tumbar una operación cerrada.",
                    "questions": [
                        {
                            "question": "El comprador firmó la reserva pero llama al otro día diciendo que 'no está seguro'. ¿Qué hacés?",
                            "options": [
                                "Le devolvés la reserva y listo",
                                "Escuchás qué lo preocupa, validás su ansiedad (es normal), y repasás las razones por las que decidió comprar. Si persiste, le das 24hs más para pensar",
                                "Le decís que la reserva es irrevocable",
                                "Le ofrecés un descuento"
                            ],
                            "correct": 1,
                            "explanation": "El 'remordimiento del comprador' es normal en inmobiliaria. La mayoría se resuelve escuchando, validando y recordando la motivación original."
                        },
                        {
                            "question": "¿Qué documento necesitás tener listo ANTES de la firma de boleto?",
                            "options": [
                                "Solo el boleto",
                                "Informe de dominio actualizado, libre deuda de expensas, impuestos al día, verificación de inhibiciones del vendedor",
                                "El título de propiedad original solamente",
                                "La escritura del departamento"
                            ],
                            "correct": 1,
                            "explanation": "Un profesional llega a la firma con toda la documentación verificada. Descubrir un problema en la firma es inaceptable y muestra falta de preparación."
                        }
                    ],
                },
            },
        ],
    },
]


# ============================================================
# INDUSTRIA DEMO — Empresa + Onboarding Journey 7 días
# ============================================================
INDUSTRIA_COMPANY = {
    "id": uuid.UUID("a0000000-0000-0000-0000-000000000003"),
    "name": "Industria Demo",
    "slug": "industria-demo",
    "email_domain": "industria.app",
    "industry": "manufactura",
    "plan": "pro",
    "is_active": True,
    "settings": {},
}

ONBOARDING_PATH = {
    "id": uuid.UUID("b0000000-0000-0000-0000-000000000003"),
    "title": "Onboarding: De cero a operador en 7 días",
    "description": "Tu journey de incorporación gamificado. Completá las misiones de cada nivel para convertirte en un operador certificado.",
    "industry": "onboarding",
    "level": "beginner",
    "company_id": uuid.UUID("a0000000-0000-0000-0000-000000000003"),
    "xp_reward": 500,
    "order_index": 0,
    "is_published": True,
}

ONBOARDING_MODULES = [
    # ── Nivel 1 — Explorador (días 1-2) ──────────────────────
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000001"),
        "path_id": uuid.UUID("b0000000-0000-0000-0000-000000000003"),
        "title": "Nivel 1 — Explorador",
        "description": "Días 1 y 2: conocé la planta y orientate en el terreno.",
        "order_index": 0,
        "xp_reward": 70,
        "estimated_minutes": 20,
        "is_published": True,
        "lessons": [
            {
                "title": "Bienvenida a la planta",
                "lesson_type": "theory",
                "order_index": 0,
                "xp_reward": 30,
                "estimated_minutes": 8,
                "content": {
                    "text": "Bienvenido a tu primer día. Antes de operar cualquier máquina o proceso, necesitás conocer el terreno: quiénes son tus compañeros de turno, dónde están las salidas de emergencia, cuáles son las zonas restringidas y qué significa cada color en el piso de la planta.\n\nEn manufactura, el conocimiento del entorno físico no es opcional — es seguridad, es eficiencia y es la base de todo lo que viene después.",
                    "key_points": [
                        "Identificá los 3 colores de piso más comunes: amarillo (tránsito), rojo (peligro/emergencia), verde (seguridad)",
                        "Memorizá la ubicación de los 2 extintores más cercanos a tu puesto",
                        "Conocé el nombre de tu supervisor de turno y cómo contactarlo en caso de problema",
                        "Nunca operés una máquina sin haber leído el procedimiento operativo estándar (POE)",
                        "El check-in de inicio de turno no es burocracia — es el primer control de calidad del día",
                    ],
                    "summary": "El primer día es de observación. Antes de tocar nada, mirá, preguntá y aprendé el lenguaje físico de la planta.",
                },
            },
            {
                "title": "El mapa del área",
                "lesson_type": "challenge",
                "order_index": 1,
                "xp_reward": 40,
                "estimated_minutes": 10,
                "content": {
                    "text": "Ahora que recorriste la planta, es momento de demostrar que entendiste la distribución. Este desafío te pide que identifiques correctamente zonas, herramientas y protocolos.",
                    "questions": [
                        {
                            "question": "¿Qué significan las líneas amarillas pintadas en el piso de una planta industrial?",
                            "options": [
                                "Zona de descarte de residuos",
                                "Pasillos de tránsito peatonal y de vehículos",
                                "Área de alta temperatura",
                                "Zona de carga y descarga exclusiva",
                            ],
                            "correct": 1,
                            "explanation": "Las líneas amarillas demarcan los pasillos de circulación. Respetarlas evita accidentes con montacargas y mantiene el flujo productivo ordenado.",
                        },
                        {
                            "question": "Al inicio de cada turno, ¿cuál es el primer paso antes de operar tu puesto?",
                            "options": [
                                "Encender la máquina y verificar que funcione",
                                "Registrar el check-in y revisar el estado del turno anterior en la bitácora",
                                "Pedir las herramientas al depósito",
                                "Reportarse con el supervisor de otra área",
                            ],
                            "correct": 1,
                            "explanation": "La bitácora del turno anterior te dice qué problemas hubo, qué quedó pendiente y si hay alguna alerta activa. Es información crítica antes de arrancar.",
                        },
                        {
                            "question": "¿Cuándo debés usar los EPP (equipos de protección personal)?",
                            "options": [
                                "Solo cuando el supervisor está mirando",
                                "Únicamente en zonas señalizadas como peligrosas",
                                "Siempre que estés dentro del área de producción, sin excepciones",
                                "Solo al manipular químicos o materiales peligrosos",
                            ],
                            "correct": 2,
                            "explanation": "Los EPP son obligatorios en todo el área de producción, sin importar la tarea. Un accidente puede ocurrir en cualquier momento — la protección no es situacional.",
                        },
                    ],
                },
            },
        ],
    },
    # ── Nivel 2 — Operador (días 3-5) ────────────────────────
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000002"),
        "path_id": uuid.UUID("b0000000-0000-0000-0000-000000000003"),
        "title": "Nivel 2 — Operador",
        "description": "Días 3 a 5: entendé el ciclo del ticket y ejecutá tu primer trabajo real.",
        "order_index": 1,
        "xp_reward": 110,
        "estimated_minutes": 25,
        "is_published": True,
        "lessons": [
            {
                "title": "El ciclo del ticket",
                "lesson_type": "quiz",
                "order_index": 0,
                "xp_reward": 50,
                "estimated_minutes": 10,
                "content": {
                    "text": "Cada tarea en la planta se gestiona a través de un ticket de trabajo: una orden que documenta qué hay que hacer, quién lo hace, en qué tiempo y con qué resultado. Entender el ciclo completo del ticket es entender cómo fluye el trabajo.",
                    "questions": [
                        {
                            "question": "¿Cuál es el primer estado de un ticket cuando se genera una orden de trabajo?",
                            "options": [
                                "En progreso",
                                "Pendiente de asignación",
                                "Cerrado",
                                "En revisión de calidad",
                            ],
                            "correct": 1,
                            "explanation": "Todo ticket nace como 'Pendiente de asignación'. Solo cuando un operador lo toma y confirma, pasa a 'En progreso'. Esto garantiza trazabilidad desde el origen.",
                        },
                        {
                            "question": "¿Cuándo podés cerrar un ticket de trabajo?",
                            "options": [
                                "Cuando terminaste la tarea física, aunque falte documentación",
                                "Solo cuando el supervisor lo aprueba, sin importar si terminaste",
                                "Cuando la tarea está completa, documentada y verificada por calidad",
                                "Cuando pasaron 8 horas desde que lo tomaste",
                            ],
                            "correct": 2,
                            "explanation": "Un ticket cerrado incorrectamente genera problemas río abajo. La tripleta completa es: tarea ejecutada + documentación completa + verificación de calidad.",
                        },
                        {
                            "question": "Si encontrás un problema no contemplado en el ticket durante la ejecución, ¿qué hacés?",
                            "options": [
                                "Lo resolvés por tu cuenta para no perder tiempo",
                                "Ignorás el problema y cerrás el ticket igual",
                                "Pausás el ticket, documentás el hallazgo y avisás al supervisor",
                                "Transferís el ticket a otro operador",
                            ],
                            "correct": 2,
                            "explanation": "Un problema no reportado es un problema que se repetirá. Pausar, documentar y escalar es el procedimiento correcto — protege tu trabajo y mejora el proceso.",
                        },
                    ],
                },
            },
            {
                "title": "Primer ticket real",
                "lesson_type": "challenge",
                "order_index": 1,
                "xp_reward": 60,
                "estimated_minutes": 12,
                "content": {
                    "text": "Este es tu primer ticket real simulado. Leé la orden de trabajo, tomá decisiones como operador y demostrá que entendiste el proceso.",
                    "questions": [
                        {
                            "question": "Tu ticket dice: 'Cambio de filtro de aire en Línea 3 — Urgente'. Al llegar, notás que el filtro correcto no está en el stock del puesto. ¿Qué hacés?",
                            "options": [
                                "Usás el filtro más parecido que encontrés para no demorar",
                                "Cerrás el ticket como 'No se pudo ejecutar' y seguís con otro",
                                "Registrás el faltante en la bitácora, avisás a tu supervisor y solicitás el insumo al depósito antes de continuar",
                                "Esperás hasta el próximo turno para que llegue el material",
                            ],
                            "correct": 2,
                            "explanation": "Nunca improvises con piezas incorrectas — en manufactura eso puede causar fallas en cascada. El procedimiento es: documentar, escalar, solicitar. Solo entonces ejecutar.",
                        },
                        {
                            "question": "Terminaste la tarea. El sistema te pide ingresar el tiempo real de ejecución. Tu estimación fue 30 min pero tardaste 55 min. ¿Qué ingresás?",
                            "options": [
                                "30 min, para no quedar mal en las métricas",
                                "55 min con una nota explicando el motivo de la demora",
                                "0 min porque el tiempo ya pasó y no importa",
                                "Un promedio entre los dos tiempos",
                            ],
                            "correct": 1,
                            "explanation": "Los datos reales son oro para la mejora continua. Si tardaste 55 min con una causa justificada, ese dato ayuda a recalibrar las estimaciones futuras. Falsear métricas destruye la confianza del sistema.",
                        },
                    ],
                },
            },
        ],
    },
    # ── Nivel 3 — Especialista (días 6-7) ────────────────────
    {
        "id": uuid.UUID("c0000000-0000-0000-0000-000000000003"),
        "path_id": uuid.UUID("b0000000-0000-0000-0000-000000000003"),
        "title": "Nivel 3 — Especialista",
        "description": "Días 6 y 7: resolvé situaciones complejas y obtené tu certificación.",
        "order_index": 2,
        "xp_reward": 150,
        "estimated_minutes": 30,
        "is_published": True,
        "lessons": [
            {
                "title": "Diagnóstico de proceso",
                "lesson_type": "roleplay",
                "order_index": 0,
                "xp_reward": 70,
                "estimated_minutes": 15,
                "content": {
                    "scenario": "Son las 14:30 del turno tarde. La Línea 2 empieza a producir piezas con rebabas visibles — defecto de calidad nivel 2. Hay un pedido urgente de 200 unidades para despachar a las 17:00. El supervisor no está disponible en este momento. Sos el operador con más horas en el turno.\n\nDescribí los pasos que tomarías: ¿parás la línea o seguís produciendo? ¿a quién avisás primero? ¿cómo documentás el incidente?",
                    "objective": "Demostrar criterio para gestionar un defecto de calidad bajo presión de tiempo, priorizando correctamente calidad, comunicación y documentación.",
                    "evaluation_criteria": [
                        "Parar la línea inmediatamente ante un defecto detectado",
                        "Notificar a supervisor/líder de turno aunque no esté disponible de forma directa",
                        "No despachar piezas defectuosas bajo ninguna circunstancia",
                        "Documentar el incidente con hora, cantidad afectada y descripción del defecto",
                        "Proponer acción correctiva o pedir asistencia técnica",
                    ],
                },
            },
            {
                "title": "Certificación: Operador Junior",
                "lesson_type": "challenge",
                "order_index": 1,
                "xp_reward": 80,
                "estimated_minutes": 15,
                "content": {
                    "text": "Esta es tu evaluación final de los 7 días. Respondé correctamente para obtener la certificación de Operador Junior y el badge 🎓 Especialista.",
                    "questions": [
                        {
                            "question": "¿Cuál es la prioridad número 1 en el piso de una planta industrial?",
                            "options": [
                                "Cumplir los tiempos de producción",
                                "Mantener la calidad del producto",
                                "La seguridad de las personas",
                                "Minimizar el desperdicio de materiales",
                            ],
                            "correct": 2,
                            "explanation": "Seguridad siempre primero. Ninguna métrica de productividad o calidad vale un accidente. En manufactura esto es un valor no negociable.",
                        },
                        {
                            "question": "Un compañero nuevo te pide que le enseñes un 'atajo' que no está en el procedimiento. ¿Qué hacés?",
                            "options": [
                                "Se lo mostrás porque funciona y ahorra tiempo",
                                "Se lo mostrás pero le pedís discreción",
                                "Le explicás que los atajos no documentados son riesgos — si es una mejora real, hay que validarla y actualizar el POE",
                                "Lo ignorás y no le respondés",
                            ],
                            "correct": 2,
                            "explanation": "Los atajos no documentados son fuentes de accidentes y defectos. Si es una mejora genuina, el camino es proponer la actualización del procedimiento. Así se construye una cultura de mejora continua.",
                        },
                        {
                            "question": "Al final de tu turno, la bitácora del turno siguiente ya tiene información registrada incorrectamente por un error tuyo. ¿Qué hacés?",
                            "options": [
                                "No hacés nada — ya fue, es problema del siguiente turno",
                                "Borrás el registro antes de irte",
                                "Corrección: hacés una enmienda firmada con hora y tu nombre, explicando el error",
                                "Le mandás un mensaje privado al supervisor sin documentar nada",
                            ],
                            "correct": 2,
                            "explanation": "Las bitácoras son documentos de trazabilidad. Nunca se borran — se enmiendan. Una enmienda firmada y fechada mantiene la integridad del registro y demuestra responsabilidad.",
                        },
                        {
                            "question": "Completaste tu onboarding de 7 días. ¿Cuál es el mejor indicador de que estás listo para operar de forma independiente?",
                            "options": [
                                "Memorizaste todos los procedimientos de memoria",
                                "No hiciste ningún error en la semana",
                                "Sabés dónde encontrar la información que necesitás y a quién preguntar cuando no sabés",
                                "El supervisor te dijo que sos el mejor del turno",
                            ],
                            "correct": 2,
                            "explanation": "Nadie memoriza todo. Un operador competente sabe que el conocimiento está en los procedimientos y en el equipo. Saber buscar y preguntar es la meta-habilidad más valiosa.",
                        },
                    ],
                },
            },
        ],
    },
]

# ── Usuarios demo de Industria Demo ──────────────────────────
INDUSTRIA_USERS = [
    {
        "email": "nuevo@industria.app",
        "full_name": "Nuevo Empleado",
        "role": "learner",
        "onboarding_done": False,
    },
    {
        "email": "admin@industria.app",
        "full_name": "Admin Industria",
        "role": "manager",
        "onboarding_done": True,
    },
]


async def seed():
    print("🌱 Seeding SalesLeap database...")

    async with async_session() as db:
        # Check if data already exists
        result = await db.execute(text("SELECT COUNT(*) FROM learning_paths"))
        count = result.scalar()
        if count and count > 0:
            print(f"⚠️  Ya hay {count} paths en la base. ¿Querés limpiar y re-seedear? (y/n)")
            resp = input().strip().lower()
            if resp != "y":
                print("❌ Seed cancelado.")
                return
            # Clean existing content data
            await db.execute(text("DELETE FROM lessons"))
            await db.execute(text("DELETE FROM modules"))
            await db.execute(text("DELETE FROM learning_paths"))
            await db.execute(text("DELETE FROM companies WHERE id IN ('a0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002')"))
            await db.commit()
            print("🗑️  Datos anteriores limpiados.")

        # Insert companies
        for c in COMPANIES:
            company = Company(**c)
            db.add(company)
        await db.flush()
        print(f"✅ {len(COMPANIES)} empresas creadas")

        # Insert paths
        for path_data in [AUTO_PATH, INMOB_PATH]:
            path = LearningPath(**path_data)
            db.add(path)
        await db.flush()
        print("✅ 2 learning paths creados")

        # Insert modules and lessons
        total_modules = 0
        total_lessons = 0
        for modules_data in [AUTO_MODULES, INMOB_MODULES]:
            for mod_data in modules_data:
                lessons_data = mod_data.pop("lessons")
                module = Module(**mod_data)
                db.add(module)
                await db.flush()
                total_modules += 1

                for lesson_data in lessons_data:
                    lesson = Lesson(
                        module_id=module.id,
                        is_published=True,
                        **lesson_data,
                    )
                    db.add(lesson)
                    total_lessons += 1

        # ── Industria Demo: empresa + onboarding path ──
        import copy as _copy
        industria = Company(**INDUSTRIA_COMPANY)
        db.add(industria)
        await db.flush()

        onb_path = LearningPath(**ONBOARDING_PATH)
        db.add(onb_path)
        await db.flush()

        for mod_data in _copy.deepcopy(ONBOARDING_MODULES):
            lessons_data = mod_data.pop("lessons")
            module = Module(**mod_data)
            db.add(module)
            await db.flush()
            total_modules += 1
            for lesson_data in lessons_data:
                db.add(Lesson(module_id=module.id, is_published=True, **lesson_data))
                total_lessons += 1

        # ── Usuarios demo de Industria ──
        from datetime import datetime, timezone
        for u_data in INDUSTRIA_USERS:
            user = User(
                email=u_data["email"],
                full_name=u_data["full_name"],
                role=UserRole(u_data["role"]),
                company_id=INDUSTRIA_COMPANY["id"],
                industry="manufactura",
                experience_level="beginner",
                email_verified=True,
                onboarding_done=u_data["onboarding_done"],
                is_active=True,
            )
            db.add(user)
            await db.flush()
            # Auto-asignar onboarding path al usuario learner
            if not u_data["onboarding_done"]:
                db.add(UserPathProgress(
                    user_id=user.id,
                    path_id=ONBOARDING_PATH["id"],
                    status=ProgressStatus.in_progress,
                    started_at=datetime.now(timezone.utc),
                ))

        await db.commit()
        print(f"✅ {total_modules} módulos creados")
        print(f"✅ {total_lessons} lecciones creadas")
        print(f"✅ Industria Demo: empresa + onboarding journey 7 días + 2 usuarios")

        # Summary
        print("\n" + "=" * 50)
        print("📊 RESUMEN DEL SEED")
        print("=" * 50)
        print(f"  Empresas:  {len(COMPANIES) + 1}")
        print(f"  Paths:     3")
        print(f"  Módulos:   {total_modules}")
        print(f"  Lecciones: {total_lessons}")
        print(f"  Badges:    (ya existentes en schema.sql)")
        print("=" * 50)
        print("\n🎉 ¡Seed completado! La demo está lista.")
        print("   Ruta auto:  'Venta Consultiva Automotriz' (3 módulos, 12 lecciones)")
        print("   Ruta inmob: 'Cierre Inmobiliario Profesional' (3 módulos, 12 lecciones)")
        print("   Onboarding: 'De cero a operador en 7 días' (3 niveles, 6 lecciones)")


if __name__ == "__main__":
    asyncio.run(seed())
