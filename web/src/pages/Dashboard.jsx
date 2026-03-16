import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [badges, setBadges] = useState([]);
  const [paths, setPaths] = useState([]);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [b, p, pr] = await Promise.all([
          api.getBadges(),
          api.getPaths(user?.industry),
          api.getProgress(),
        ]);
        setBadges(b);
        setPaths(p);
        setProgress(pr);
      } catch {
        // ignore for now
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user?.industry]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin text-3xl">⏳</div>
      </div>
    );
  }

  const xpToNext = 500 - (user.total_xp % 500);
  const xpPercent = ((user.total_xp % 500) / 500) * 100;

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">
            <span className="text-primary">Sales</span>Leap
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/coach"
            className="text-sm bg-primary/10 text-primary hover:bg-primary/20 px-3 py-1.5 rounded-lg transition"
          >
            🧠 AI Coach
          </Link>
          <span className="text-gray-400 text-sm hidden md:block">{user.email}</span>
          <button
            onClick={logout}
            className="text-sm text-gray-400 hover:text-white transition"
          >
            Salir
          </button>
        </div>
      </div>

      {/* Greeting */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold">
          Hola, {user.full_name.split(' ')[0]} 👋
        </h2>
        <p className="text-gray-400 text-sm">
          {user.streak_current > 0
            ? `🔥 ${user.streak_current} días de racha — ¡seguí así!`
            : 'Completá una lección hoy para arrancar tu racha'}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <StatCard label="XP Total" value={user.total_xp.toLocaleString()} icon="⭐" />
        <StatCard label="Nivel" value={user.level} icon="📊" />
        <StatCard label="Racha" value={`${user.streak_current} días`} icon="🔥" />
        <StatCard label="Lecciones" value={progress?.total_lessons_completed || 0} icon="📚" />
      </div>

      {/* XP Progress Bar */}
      <div className="bg-surface rounded-xl p-4 mb-8">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-400">Nivel {user.level}</span>
          <span className="text-gray-400">{xpToNext} XP para nivel {user.level + 1}</span>
        </div>
        <div className="h-3 bg-surface-light rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-500"
            style={{ width: `${xpPercent}%` }}
          />
        </div>
      </div>

      {/* Badges */}
      {badges.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-3">Tus badges</h3>
          <div className="flex flex-wrap gap-3">
            {badges.map((b) => (
              <div
                key={b.id}
                className="bg-surface rounded-xl px-4 py-3 flex items-center gap-2 border border-gray-800"
              >
                <span className="text-2xl">{b.icon}</span>
                <div>
                  <div className="text-sm font-medium">{b.name}</div>
                  <div className="text-xs text-gray-500">{b.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Learning Paths */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-3">Rutas de aprendizaje</h3>
        {paths.length === 0 ? (
          <div className="bg-surface rounded-xl p-6 text-center text-gray-400">
            No hay rutas disponibles todavía.
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {paths.map((path) => (
              <PathCard key={path.id} path={path} />
            ))}
          </div>
        )}
      </div>

      {/* Coach CTA */}
      <Link
        to="/coach"
        className="block bg-gradient-to-r from-primary/20 to-accent/20 border border-primary/30 rounded-xl p-5 hover:border-primary/60 transition mb-8"
      >
        <div className="flex items-center gap-4">
          <div className="text-3xl">🧠</div>
          <div>
            <h3 className="font-semibold text-white">AI Sales Coach</h3>
            <p className="text-sm text-gray-400">Preguntale lo que quieras sobre ventas, practicá roleplays o pedí tips personalizados</p>
          </div>
          <span className="text-gray-400 ml-auto">→</span>
        </div>
      </Link>
    </div>
  );
}

function StatCard({ label, value, icon }) {
  return (
    <div className="bg-surface rounded-xl p-4 text-center">
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  );
}

function PathCard({ path }) {
  const levelColors = {
    beginner: 'text-green-400 bg-green-400/10',
    intermediate: 'text-amber-400 bg-amber-400/10',
    advanced: 'text-red-400 bg-red-400/10',
  };
  const levelLabels = { beginner: 'Principiante', intermediate: 'Intermedio', advanced: 'Avanzado' };
  const color = levelColors[path.level] || 'text-gray-400 bg-gray-400/10';

  return (
    <Link
      to={`/path/${path.id}`}
      className="bg-surface rounded-xl p-5 border border-gray-800 hover:border-primary/50 transition block"
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold text-white">{path.title}</h4>
        <span className={`text-xs px-2 py-0.5 rounded-full ${color}`}>
          {levelLabels[path.level] || path.level}
        </span>
      </div>
      <p className="text-sm text-gray-400 mb-3 line-clamp-2">{path.description}</p>
      <div className="flex items-center gap-3 text-xs text-gray-500">
        <span>⭐ {path.xp_reward} XP</span>
        <span>📖 {path.industry}</span>
      </div>
    </Link>
  );
}
