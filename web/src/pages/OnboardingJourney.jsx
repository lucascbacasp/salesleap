import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

const LESSON_TYPE_ICON = {
  theory: '📖',
  quiz: '🧠',
  roleplay: '🎭',
  challenge: '⚡',
};

export default function OnboardingJourney() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [mission, setMission] = useState(null);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const firstName = user?.full_name?.split(' ')[0] || 'allá';

  useEffect(() => {
    (async () => {
      try {
        const m = await api.getMission();
        setMission(m);

        if (!m.assigned_path) {
          // No journey path assigned — send to sales quiz
          navigate('/onboarding', { replace: true });
          return;
        }

        const mods = await api.getPathModules(m.assigned_path.id);
        setModules(mods);
      } catch (err) {
        setError(err.detail || 'Error al cargar tu ruta');
      } finally {
        setLoading(false);
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-400">Preparando tu ruta...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl p-8 max-w-md w-full text-center">
          <div className="text-5xl mb-4">❌</div>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-primary hover:underline"
          >
            Ir al dashboard
          </button>
        </div>
      </div>
    );
  }

  const ap = mission?.assigned_path;
  const nextLesson = mission?.next_lesson;
  const completedToday = mission?.completed_today ?? 0;
  const target = mission?.target ?? 3;

  return (
    <div className="min-h-screen bg-background p-4 pb-16">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="mb-8 pt-6">
          <h1 className="text-2xl font-bold text-white leading-tight">
            Bienvenido, {firstName}.
          </h1>
          <p className="text-primary font-semibold mt-1 text-lg">
            Tu semana de habilitación empieza hoy.
          </p>
          {ap && (
            <p className="text-gray-400 text-sm mt-2">{ap.description}</p>
          )}
        </div>

        {/* Overall progress */}
        {ap && (
          <div className="bg-surface rounded-2xl p-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400">Progreso general</span>
              <span className="text-sm font-semibold text-primary">{ap.progress_pct}%</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-3">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${ap.progress_pct}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500">
              <span>{ap.completed_lessons} de {ap.total_lessons} lecciones completadas</span>
              <span>{ap.total_lessons - ap.completed_lessons} restantes</span>
            </div>
          </div>
        )}

        {/* Daily mission */}
        <div className="bg-surface rounded-2xl p-5 mb-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-semibold text-white">🏆 Misión de hoy</h3>
              <p className="text-xs text-gray-400 mt-0.5">Completá {target} lecciones</p>
            </div>
            {mission?.is_completed && (
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full font-semibold">
                ✓ Completada
              </span>
            )}
          </div>
          <div className="flex gap-2">
            {Array.from({ length: target }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 h-2.5 rounded-full ${
                  i < completedToday ? 'bg-primary' : 'bg-gray-700'
                }`}
              />
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">{completedToday} / {target} lecciones hoy</p>
        </div>

        {/* CTA — next lesson */}
        {nextLesson && (
          <button
            onClick={() => navigate(`/lesson/${nextLesson.id}`)}
            className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-4 rounded-xl transition mb-6 flex items-center justify-center gap-2 text-base"
          >
            <span>{LESSON_TYPE_ICON[nextLesson.lesson_type] || '▶'}</span>
            Empezar mi primera lección
            <span className="text-primary-light text-sm font-normal ml-1">
              +{nextLesson.xp_reward} XP
            </span>
          </button>
        )}

        {/* Module list */}
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Tu programa completo
        </h2>

        <div className="space-y-4">
          {modules.map((mod, modIdx) => {
            const totalLessons = mod.lessons.length;
            const completedLessons = mod.lessons.filter((l) => l.completed).length;
            const modDone = totalLessons > 0 && completedLessons === totalLessons;

            return (
              <div key={mod.id} className="bg-surface rounded-2xl overflow-hidden">
                {/* Module header */}
                <div className="flex items-start justify-between p-5 pb-3">
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 mt-0.5 ${
                        modDone
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-primary/20 text-primary'
                      }`}
                    >
                      {modDone ? '✓' : modIdx + 1}
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{mod.title}</h3>
                      {mod.description && (
                        <p className="text-xs text-gray-400 mt-0.5">{mod.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
                        <span>⭐ {mod.xp_reward} XP</span>
                        {mod.estimated_minutes && <span>⏱ {mod.estimated_minutes} min</span>}
                        <span>{completedLessons}/{totalLessons} lecciones</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Lessons */}
                {mod.lessons.length > 0 && (
                  <div className="border-t border-gray-800">
                    {mod.lessons.map((lesson, lesIdx) => (
                      <button
                        key={lesson.id}
                        onClick={() => navigate(`/lesson/${lesson.id}`)}
                        className={`w-full text-left flex items-center gap-3 px-5 py-3 transition hover:bg-surface-light ${
                          lesIdx < mod.lessons.length - 1 ? 'border-b border-gray-800/60' : ''
                        }`}
                      >
                        <span
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
                            lesson.completed
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-gray-700 text-gray-400'
                          }`}
                        >
                          {lesson.completed ? '✓' : LESSON_TYPE_ICON[lesson.lesson_type] || '○'}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p
                            className={`text-sm font-medium truncate ${
                              lesson.completed ? 'text-gray-400 line-through' : 'text-white'
                            }`}
                          >
                            {lesson.title}
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {lesson.lesson_type} · +{lesson.xp_reward} XP
                            {lesson.estimated_minutes ? ` · ${lesson.estimated_minutes} min` : ''}
                          </p>
                        </div>
                        {!lesson.completed && (
                          <span className="text-gray-600 text-sm">›</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
