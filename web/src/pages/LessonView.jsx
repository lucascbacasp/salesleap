import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

export default function LessonView() {
  const { lessonId } = useParams();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [result, setResult] = useState(null);
  const [feedbackDismissed, setFeedbackDismissed] = useState(false);
  const startTime = useRef(Date.now());

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getLesson(lessonId);
        setLesson(data);
      } catch {
        // error
      } finally {
        setLoading(false);
      }
    }
    load();
    startTime.current = Date.now();
  }, [lessonId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin text-3xl">⏳</div>
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400">Lección no encontrada</p>
      </div>
    );
  }

  const typeLabels = { theory: 'Teoría', quiz: 'Quiz', roleplay: 'Roleplay', challenge: 'Desafío' };
  const typeIcons = { theory: '📖', quiz: '❓', roleplay: '🎭', challenge: '⚡' };

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white transition">
          ← Volver
        </button>
        <span className="text-xs text-gray-500 bg-surface px-3 py-1 rounded-full">
          {typeIcons[lesson.lesson_type]} {typeLabels[lesson.lesson_type]} · {lesson.estimated_minutes} min · {lesson.xp_reward} XP
        </span>
      </div>

      <h1 className="text-2xl font-bold text-white mb-6">{lesson.title}</h1>

      {/* Render based on type */}
      {lesson.lesson_type === 'theory' && (
        <TheoryLesson lesson={lesson} onComplete={handleComplete} completing={completing} />
      )}
      {(lesson.lesson_type === 'quiz' || lesson.lesson_type === 'challenge') && (
        <QuizLesson lesson={lesson} onComplete={handleComplete} completing={completing} />
      )}
      {lesson.lesson_type === 'roleplay' && (
        <RoleplayLesson lesson={lesson} onComplete={handleComplete} completing={completing} />
      )}

      {/* AI Feedback overlay (shown before completion modal for roleplays) */}
      {result && result.ai_feedback && !feedbackDismissed && (
        <FeedbackOverlay feedback={result.ai_feedback} onContinue={() => setFeedbackDismissed(true)} />
      )}

      {/* Completion result overlay */}
      {result && (!result.ai_feedback || feedbackDismissed) && (
        <CompletionModal result={result} onClose={() => navigate(-1)} />
      )}
    </div>
  );

  async function handleComplete(score = null, answers = null) {
    setCompleting(true);
    try {
      const timeSpent = Math.floor((Date.now() - startTime.current) / 1000);
      const data = await api.completeLesson(lessonId, {
        score,
        time_spent_sec: timeSpent,
        answers,
      });
      setResult(data);
      await refreshUser();
    } catch (err) {
      console.error('Error completing lesson:', err);
    } finally {
      setCompleting(false);
    }
  }
}

// =============================================
// THEORY LESSON
// =============================================
function TheoryLesson({ lesson, onComplete, completing }) {
  const content = lesson.content;
  return (
    <div>
      <div className="bg-surface rounded-2xl p-6 mb-6">
        <div className="prose-invert">
          {content.text?.split('\n\n').map((p, i) => (
            <p key={i} className="text-gray-300 mb-4 leading-relaxed">{p}</p>
          ))}
        </div>
      </div>

      {content.key_points && (
        <div className="bg-surface rounded-2xl p-6 mb-6">
          <h3 className="text-lg font-semibold mb-3">📌 Puntos clave</h3>
          <ul className="space-y-2">
            {content.key_points.map((point, i) => (
              <li key={i} className="flex items-start gap-2 text-gray-300">
                <span className="text-primary mt-0.5">•</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {content.summary && (
        <div className="bg-primary/10 border border-primary/30 rounded-xl p-4 mb-6">
          <span className="text-xs text-primary font-semibold block mb-1">💡 Resumen</span>
          <p className="text-gray-300 text-sm">{content.summary}</p>
        </div>
      )}

      <button
        onClick={() => onComplete(100)}
        disabled={completing}
        className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
      >
        {completing ? 'Completando...' : '✅ Marcar como completada'}
      </button>
    </div>
  );
}

// =============================================
// QUIZ / CHALLENGE LESSON
// =============================================
function QuizLesson({ lesson, onComplete, completing }) {
  const questions = lesson.content.questions || [];
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [answers, setAnswers] = useState([]);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);

  const q = questions[current];

  const handleSelect = (idx) => {
    if (showFeedback) return;
    setSelected(idx);
    setShowFeedback(true);

    const isCorrect = idx === q.correct;
    const newAnswers = [
      ...answers,
      { question: q.question, answer: q.options[idx], correct: q.options[q.correct], is_correct: isCorrect },
    ];
    setAnswers(newAnswers);
    if (isCorrect) setScore((s) => s + 1);
  };

  const handleNext = () => {
    if (current < questions.length - 1) {
      setCurrent(current + 1);
      setSelected(null);
      setShowFeedback(false);
    } else {
      setFinished(true);
      const finalScore = ((score + (selected === q?.correct ? 0 : 0)) / questions.length) * 100;
      // Score is already accumulated, just pass it
      const totalCorrect = answers.filter((a) => a.is_correct).length;
      onComplete(Math.round((totalCorrect / questions.length) * 100), answers);
    }
  };

  if (!q) return null;

  return (
    <div>
      {lesson.content.text && (
        <p className="text-gray-400 mb-6">{lesson.content.text}</p>
      )}

      {/* Progress */}
      <div className="flex items-center gap-2 mb-6">
        {questions.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-all ${
              i < current ? 'bg-primary' : i === current ? 'bg-primary/50' : 'bg-gray-700'
            }`}
          />
        ))}
      </div>

      <div className="bg-surface rounded-2xl p-6 mb-4">
        <p className="text-xs text-gray-500 mb-2">Pregunta {current + 1} de {questions.length}</p>
        <h3 className="text-lg font-semibold text-white mb-5">{q.question}</h3>

        <div className="space-y-3">
          {q.options.map((opt, idx) => {
            let classes = 'border-gray-700 bg-surface-light text-gray-300';
            if (showFeedback) {
              if (idx === q.correct) classes = 'border-green-500 bg-green-500/10 text-green-300';
              else if (idx === selected && idx !== q.correct) classes = 'border-red-500 bg-red-500/10 text-red-300';
            } else if (idx === selected) {
              classes = 'border-primary bg-primary/10 text-white';
            }

            return (
              <button
                key={idx}
                onClick={() => handleSelect(idx)}
                disabled={showFeedback}
                className={`w-full text-left px-4 py-3 rounded-lg border transition ${classes}`}
              >
                <span className="text-xs text-gray-500 mr-2">{String.fromCharCode(65 + idx)}.</span>
                {opt}
              </button>
            );
          })}
        </div>

        {/* Feedback */}
        {showFeedback && q.explanation && (
          <div className={`mt-4 p-4 rounded-lg border ${
            selected === q.correct
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-amber-500/10 border-amber-500/30'
          }`}>
            <p className="text-sm font-semibold mb-1">
              {selected === q.correct ? '✅ ¡Correcto!' : '❌ No exactamente'}
            </p>
            <p className="text-sm text-gray-300">{q.explanation}</p>
          </div>
        )}
      </div>

      {showFeedback && (
        <button
          onClick={handleNext}
          disabled={completing}
          className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
        >
          {current < questions.length - 1 ? 'Siguiente pregunta →' : completing ? 'Completando...' : '🏁 Finalizar'}
        </button>
      )}
    </div>
  );
}

// =============================================
// ROLEPLAY LESSON
// =============================================
function RoleplayLesson({ lesson, onComplete, completing }) {
  const [response, setResponse] = useState('');
  const content = lesson.content;

  const handleSubmit = () => {
    if (!response.trim()) return;
    // Send the response to the backend — AI evaluation happens server-side
    onComplete(null, [{ question: content.scenario, answer: response }]);
  };

  return (
    <div>
      {/* Scenario */}
      <div className="bg-surface rounded-2xl p-6 mb-4">
        <h3 className="text-sm font-semibold text-accent mb-2">🎭 Escenario</h3>
        <p className="text-gray-300 leading-relaxed">{content.scenario}</p>
      </div>

      {/* Objective */}
      {content.objective && (
        <div className="bg-primary/10 border border-primary/30 rounded-xl p-4 mb-4">
          <span className="text-xs text-primary font-semibold block mb-1">🎯 Tu objetivo</span>
          <p className="text-sm text-gray-300">{content.objective}</p>
        </div>
      )}

      {/* Evaluation criteria */}
      {content.evaluation_criteria && (
        <div className="bg-surface rounded-xl p-4 mb-4">
          <span className="text-xs text-gray-400 font-semibold block mb-2">Se evalúa:</span>
          <div className="flex flex-wrap gap-2">
            {content.evaluation_criteria.map((c, i) => (
              <span key={i} className="text-xs bg-surface-light text-gray-400 px-2 py-1 rounded-full">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Response area */}
      <textarea
        value={response}
        onChange={(e) => setResponse(e.target.value)}
        placeholder="Escribí tu respuesta como si estuvieras hablando con el cliente..."
        rows={6}
        className="w-full bg-surface border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary transition resize-none mb-4"
        disabled={completing}
      />
      <button
        onClick={handleSubmit}
        disabled={!response.trim() || completing}
        className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
      >
        {completing ? '🧠 Evaluando con IA...' : '🚀 Enviar respuesta'}
      </button>
    </div>
  );
}

// =============================================
// AI FEEDBACK OVERLAY (shown before completion modal)
// =============================================
function FeedbackOverlay({ feedback, onContinue }) {
  const [show, setShow] = useState(false);
  useEffect(() => { setTimeout(() => setShow(true), 50); }, []);

  // Split feedback into main + tip
  const parts = feedback.split('\n\n💡 Tip: ');
  const mainFeedback = parts[0];
  const tip = parts[1] || null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className={`bg-surface rounded-2xl p-8 max-w-md w-full transition-all duration-500 ${show ? 'scale-100 opacity-100' : 'scale-90 opacity-0'}`}>
        <div className="text-center mb-4">
          <div className="text-4xl mb-2">🧠</div>
          <h2 className="text-xl font-bold">Feedback del AI Coach</h2>
        </div>

        <div className="bg-surface-light rounded-xl p-5 mb-4">
          <p className="text-gray-300 leading-relaxed">{mainFeedback}</p>
        </div>

        {tip && (
          <div className="bg-accent/10 border border-accent/30 rounded-xl p-4 mb-4">
            <span className="text-xs text-accent font-semibold block mb-1">💡 Tip para aplicar hoy</span>
            <p className="text-sm text-gray-300">{tip}</p>
          </div>
        )}

        <button
          onClick={onContinue}
          className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition"
        >
          Ver mis puntos →
        </button>
      </div>
    </div>
  );
}

// =============================================
// COMPLETION MODAL
// =============================================
function CompletionModal({ result, onClose }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    setTimeout(() => setShow(true), 50);
  }, []);

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className={`bg-surface rounded-2xl p-8 max-w-md w-full text-center transition-all duration-500 ${show ? 'scale-100 opacity-100' : 'scale-90 opacity-0'}`}>
        <div className="text-5xl mb-4 animate-bounce">🎉</div>
        <h2 className="text-2xl font-bold mb-2">¡Lección completada!</h2>

        {/* XP earned with animation */}
        <div className="bg-accent/10 border border-accent/30 rounded-xl p-4 mb-4 inline-block">
          <span className="text-3xl font-bold text-accent">+{result.xp_earned} XP</span>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-surface-light rounded-lg p-3">
            <span className="text-xs text-gray-400 block">XP Total</span>
            <span className="text-lg font-bold text-white">{result.total_xp}</span>
          </div>
          <div className="bg-surface-light rounded-lg p-3">
            <span className="text-xs text-gray-400 block">Nivel</span>
            <span className="text-lg font-bold text-white">{result.new_level}</span>
          </div>
        </div>

        {result.streak_current > 0 && (
          <p className="text-sm text-gray-400 mb-2">🔥 {result.streak_current} días de racha</p>
        )}

        {/* Badges earned */}
        {result.badges_earned?.length > 0 && (
          <div className="mb-4">
            <p className="text-sm text-gray-400 mb-2">🏆 ¡Nuevos badges!</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {result.badges_earned.map((badge, i) => (
                <span key={i} className="bg-primary/20 text-primary px-3 py-1 rounded-full text-sm animate-pulse">
                  {badge}
                </span>
              ))}
            </div>
          </div>
        )}

        {result.ai_feedback && (
          <div className="bg-primary/10 border border-primary/30 rounded-lg p-3 mb-4 text-left">
            <span className="text-xs text-primary block mb-1">💬 Feedback</span>
            <p className="text-sm text-gray-300">{result.ai_feedback}</p>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition"
        >
          Continuar
        </button>
      </div>
    </div>
  );
}
