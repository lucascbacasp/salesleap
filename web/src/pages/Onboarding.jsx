import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

const QUESTIONS = [
  {
    question: '¿Cómo manejás una objeción de precio?',
    options: [
      'Bajo el precio inmediatamente',
      'Muestro el valor antes de hablar de precio',
      'Ignoro la objeción y sigo presentando',
      'Le digo que es el mejor precio del mercado',
    ],
  },
  {
    question: '¿Qué hacés cuando el cliente dice "lo pienso"?',
    options: [
      'Le digo que está bien y espero',
      'Pregunto qué lo haría decidir hoy',
      'Le ofrezco un descuento',
      'No hago nada, es su decisión',
    ],
  },
  {
    question: '¿Cómo preparás una reunión de ventas?',
    options: [
      'No preparo, improviso',
      'Investigo al cliente y preparo preguntas',
      'Solo reviso el catálogo de productos',
      'Le mando un email antes con toda la info',
    ],
  },
];

const INDUSTRIES = [
  { value: 'auto', label: 'Automotriz' },
  { value: 'inmobiliaria', label: 'Inmobiliaria' },
  { value: 'b2b', label: 'B2B / Software' },
  { value: 'otro', label: 'Otro' },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState(0); // 0=industry, 1-3=questions, 4=results
  const [industry, setIndustry] = useState('');
  const [experience, setExperience] = useState(1);
  const [answers, setAnswers] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleIndustrySubmit = () => {
    if (!industry) return;
    setStep(1);
  };

  const handleAnswer = (optionText) => {
    const q = QUESTIONS[step - 1];
    const newAnswers = [...answers, { question: q.question, answer: optionText }];
    setAnswers(newAnswers);

    if (step < QUESTIONS.length) {
      setStep(step + 1);
    } else {
      submitQuiz(newAnswers);
    }
  };

  const submitQuiz = async (allAnswers) => {
    setLoading(true);
    setError('');
    try {
      const data = await api.submitOnboarding({
        industry,
        experience_years: experience,
        answers: allAnswers,
      });
      setResult(data);
      setStep(QUESTIONS.length + 1);
      await refreshUser();
    } catch (err) {
      setError(err.detail || 'Error al procesar el quiz');
    } finally {
      setLoading(false);
    }
  };

  // Industry selection
  if (step === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl p-8 max-w-lg w-full">
          <div className="text-center mb-6">
            <div className="text-4xl mb-2">👋</div>
            <h1 className="text-2xl font-bold">Bienvenido a SalesLeap</h1>
            <p className="text-gray-400 mt-1">Contanos sobre vos para personalizar tu experiencia</p>
          </div>

          <div className="space-y-3 mb-6">
            <label className="block text-sm text-gray-400">¿En qué industria vendés?</label>
            {INDUSTRIES.map((ind) => (
              <button
                key={ind.value}
                onClick={() => setIndustry(ind.value)}
                className={`w-full text-left px-4 py-3 rounded-lg border transition ${
                  industry === ind.value
                    ? 'border-primary bg-primary/10 text-white'
                    : 'border-gray-700 bg-surface-light text-gray-300 hover:border-gray-500'
                }`}
              >
                {ind.label}
              </button>
            ))}
          </div>

          <div className="mb-6">
            <label className="block text-sm text-gray-400 mb-1">Años de experiencia en ventas</label>
            <input
              type="number"
              min="0"
              max="40"
              value={experience}
              onChange={(e) => setExperience(Number(e.target.value))}
              className="w-full bg-surface-light border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-primary"
            />
          </div>

          <button
            onClick={handleIndustrySubmit}
            disabled={!industry}
            className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
          >
            Comenzar quiz nivelatorio
          </button>
        </div>
      </div>
    );
  }

  // Loading after quiz
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">🧠</div>
          <p className="text-gray-400">Analizando tus respuestas con IA...</p>
        </div>
      </div>
    );
  }

  // Results
  if (result) {
    const levelLabels = { beginner: 'Principiante', intermediate: 'Intermedio', advanced: 'Avanzado' };
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl p-8 max-w-lg w-full">
          <div className="text-center mb-6">
            <div className="text-4xl mb-2">🎯</div>
            <h2 className="text-2xl font-bold">Tu resultado</h2>
          </div>

          <div className="bg-primary/10 border border-primary/30 rounded-lg p-4 mb-4 text-center">
            <span className="text-sm text-gray-400">Tu nivel</span>
            <div className="text-2xl font-bold text-primary">{levelLabels[result.level] || result.level}</div>
          </div>

          <p className="text-gray-300 mb-4">{result.explanation}</p>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-surface-light rounded-lg p-3">
              <span className="text-xs text-gray-400 block">Fortalezas</span>
              {result.strengths.map((s, i) => (
                <span key={i} className="text-sm text-green-400 block">✓ {s}</span>
              ))}
            </div>
            <div className="bg-surface-light rounded-lg p-3">
              <span className="text-xs text-gray-400 block">A mejorar</span>
              {result.gaps.map((g, i) => (
                <span key={i} className="text-sm text-amber-400 block">→ {g}</span>
              ))}
            </div>
          </div>

          <div className="bg-accent/10 border border-accent/30 rounded-lg p-3 mb-6">
            <span className="text-xs text-accent block mb-1">💡 Quick Win</span>
            <span className="text-sm text-gray-300">{result.quick_win_tip}</span>
          </div>

          {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

          <button
            onClick={() => navigate('/dashboard')}
            className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition"
          >
            Ir al dashboard
          </button>
        </div>
      </div>
    );
  }

  // Quiz questions
  const qIndex = step - 1;
  const question = QUESTIONS[qIndex];

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl p-8 max-w-lg w-full">
        <div className="flex items-center justify-between mb-6">
          <span className="text-sm text-gray-400">Pregunta {step} de {QUESTIONS.length}</span>
          <div className="flex gap-1">
            {QUESTIONS.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 w-8 rounded-full ${i < step ? 'bg-primary' : 'bg-gray-700'}`}
              />
            ))}
          </div>
        </div>

        <h2 className="text-xl font-semibold mb-6">{question.question}</h2>

        <div className="space-y-3">
          {question.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => handleAnswer(opt)}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-700 bg-surface-light text-gray-300 hover:border-primary hover:text-white transition"
            >
              {opt}
            </button>
          ))}
        </div>

        {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
      </div>
    </div>
  );
}
