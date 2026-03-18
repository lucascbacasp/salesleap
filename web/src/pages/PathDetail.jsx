import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

export default function PathDetail() {
  const { pathId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [path, setPath] = useState(null);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedModule, setExpandedModule] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const paths = await api.getPaths();
        const p = paths.find((x) => x.id === pathId);
        setPath(p);
      } catch (err) {
        console.error('Error loading path:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [pathId]);

  // We need to load modules for this path — let's add an API call
  useEffect(() => {
    async function loadModules() {
      if (!pathId) return;
      try {
        const res = await fetch(`/api/paths/${pathId}/modules`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        if (res.ok) {
          const data = await res.json();
          setModules(data);
          if (data.length > 0) setExpandedModule(data[0].id);
        }
      } catch {
        // fallback: modules not available
      }
    }
    loadModules();
  }, [pathId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin text-3xl">⏳</div>
      </div>
    );
  }

  if (!path) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🔍</div>
          <p className="text-gray-400">Ruta no encontrada</p>
          <Link to="/dashboard" className="text-primary hover:underline mt-2 block">
            Volver al dashboard
          </Link>
        </div>
      </div>
    );
  }

  const levelLabels = { beginner: 'Principiante', intermediate: 'Intermedio', advanced: 'Avanzado' };
  const levelColors = {
    beginner: 'text-green-400 bg-green-400/10 border-green-400/30',
    intermediate: 'text-amber-400 bg-amber-400/10 border-amber-400/30',
    advanced: 'text-red-400 bg-red-400/10 border-red-400/30',
  };

  const totalLessons = modules.reduce((acc, m) => acc + (m.lessons?.length || 0), 0);
  const totalMinutes = modules.reduce((acc, m) => acc + (m.estimated_minutes || 0), 0);
  const completedLessonsCount = modules.reduce(
    (acc, m) => acc + (m.lessons?.filter((l) => l.completed)?.length || 0), 0
  );
  const progressPct = totalLessons > 0 ? Math.round((completedLessonsCount / totalLessons) * 100) : 0;

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate('/dashboard')}
          className="text-gray-400 hover:text-white transition"
        >
          ← Volver
        </button>
      </div>

      {/* Path Info */}
      <div className="bg-surface rounded-2xl p-6 mb-6">
        <div className="flex items-start justify-between mb-3">
          <h1 className="text-2xl font-bold text-white">{path.title}</h1>
          <span className={`text-xs px-3 py-1 rounded-full border ${levelColors[path.level] || ''}`}>
            {levelLabels[path.level] || path.level}
          </span>
        </div>
        <p className="text-gray-400 mb-4">{path.description}</p>

        <div className="flex items-center gap-6 text-sm text-gray-500">
          <span>📖 {path.industry}</span>
          <span>📚 {totalLessons} lecciones</span>
          <span>⏱️ ~{totalMinutes} min</span>
          <span>⭐ {path.xp_reward} XP</span>
        </div>

        {/* Overall progress bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progreso general</span>
            <span>{completedLessonsCount}/{totalLessons} lecciones · {progressPct}%</span>
          </div>
          <div className="h-2.5 bg-surface-light rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-700"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Modules accordion */}
      <div className="space-y-3">
        {modules.map((mod, i) => {
          const isExpanded = expandedModule === mod.id;
          const lessons = mod.lessons || [];

          return (
            <div key={mod.id} className="bg-surface rounded-xl overflow-hidden border border-gray-800">
              {/* Module header */}
              <button
                onClick={() => setExpandedModule(isExpanded ? null : mod.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-surface-light/50 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold">
                    {i + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{mod.title}</h3>
                    <p className="text-xs text-gray-500">{lessons.length} lecciones · {mod.estimated_minutes} min · {mod.xp_reward} XP</p>
                  </div>
                </div>
                <span className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                  ▼
                </span>
              </button>

              {/* Lessons list */}
              {isExpanded && (
                <div className="border-t border-gray-800">
                  {mod.description && (
                    <p className="text-sm text-gray-400 px-4 py-3 bg-surface-light/30">
                      {mod.description}
                    </p>
                  )}
                  {lessons.map((lesson, j) => {
                    const typeIcons = { theory: '📖', quiz: '❓', roleplay: '🎭', challenge: '⚡' };
                    const typeLabels = { theory: 'Teoría', quiz: 'Quiz', roleplay: 'Roleplay', challenge: 'Desafío' };

                    return (
                      <Link
                        key={lesson.id}
                        to={`/lesson/${lesson.id}`}
                        className="flex items-center gap-3 px-4 py-3 hover:bg-surface-light/50 transition border-t border-gray-800/50"
                      >
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                          lesson.completed ? 'bg-green-500/20 text-green-400' : 'bg-gray-800'
                        }`}>
                          {lesson.completed ? '✓' : typeIcons[lesson.lesson_type] || '📄'}
                        </div>
                        <div className="flex-1">
                          <p className={`text-sm ${lesson.completed ? 'text-gray-400' : 'text-white'}`}>
                            {lesson.title}
                          </p>
                          <p className="text-xs text-gray-500">
                            {typeLabels[lesson.lesson_type]} · {lesson.estimated_minutes} min · {lesson.xp_reward} XP
                          </p>
                        </div>
                        <span className="text-gray-600 text-sm">→</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {modules.length === 0 && (
        <div className="bg-surface rounded-xl p-8 text-center text-gray-400">
          <div className="text-3xl mb-2">📭</div>
          <p>No hay módulos disponibles en esta ruta todavía.</p>
        </div>
      )}
    </div>
  );
}
