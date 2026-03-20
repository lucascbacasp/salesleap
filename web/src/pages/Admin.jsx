import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

export default function Admin() {
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [certMap, setCertMap] = useState({});   // user_id → certificate | null
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCert, setSelectedCert] = useState(null); // { full_name, certificate }

  useEffect(() => {
    async function load() {
      if (!user?.company_id) {
        setError('No estás asociado a una empresa.');
        setLoading(false);
        return;
      }
      try {
        const [weekly, certs] = await Promise.all([
          api.getCompanyWeekly(user.company_id),
          api.getCompanyCertificates(user.company_id),
        ]);
        setData(weekly);
        // Build map user_id → certificate (may be null)
        const map = {};
        for (const entry of certs.certificates) {
          map[entry.user_id] = { full_name: entry.full_name, certificate: entry.certificate };
        }
        setCertMap(map);
      } catch (err) {
        setError(err.detail || 'Error al cargar datos');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user?.company_id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin text-3xl">⏳</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl p-8 max-w-md text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-gray-400 mb-4">{error}</p>
          <Link to="/dashboard" className="text-primary hover:underline">Volver al dashboard</Link>
        </div>
      </div>
    );
  }

  const { total_users, active_this_week, completed_target, completed_target_pct, weekly_target, team, week_start, week_end } = data;

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">
            <span className="text-primary">Sales</span>Leap
            <span className="text-sm text-gray-500 ml-2 font-normal">Admin</span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-sm text-gray-400 hover:text-white transition">
            ← Dashboard
          </Link>
          <button onClick={logout} className="text-sm text-gray-400 hover:text-white transition">
            Salir
          </button>
        </div>
      </div>

      {/* Week indicator */}
      <p className="text-sm text-gray-500 mb-6">
        Semana del {formatDate(week_start)} al {formatDate(week_end)}
      </p>

      {/* Hero metric */}
      <div className="bg-gradient-to-r from-primary/15 to-accent/15 border border-primary/30 rounded-2xl p-6 md:p-8 mb-8">
        <div className="text-center">
          <p className="text-sm text-gray-400 mb-2">
            Vendedores que completaron ≥{weekly_target} lecciones esta semana
          </p>
          <div className="flex items-baseline justify-center gap-3">
            <span className="text-6xl font-bold text-white">{completed_target}</span>
            <span className="text-2xl text-gray-500">/ {total_users}</span>
          </div>
          <div className="mt-3 max-w-xs mx-auto">
            <div className="h-3 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-700"
                style={{ width: `${completed_target_pct}%` }}
              />
            </div>
            <span className="text-sm text-gray-400 mt-1 block">{completed_target_pct}% del equipo</span>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Total vendedores" value={total_users} icon="👥" />
        <StatCard label="Activos esta semana" value={active_this_week} icon="✅" color={active_this_week > 0 ? 'text-green-400' : ''} />
        <StatCard label="Inactivos" value={total_users - active_this_week} icon="💤" color={total_users - active_this_week > 0 ? 'text-amber-400' : ''} />
      </div>

      {/* Team table */}
      <div className="bg-surface rounded-2xl overflow-hidden mb-8">
        <div className="p-5 border-b border-gray-800">
          <h3 className="font-semibold text-white">Equipo</h3>
        </div>

        {/* Desktop table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase tracking-wide border-b border-gray-800">
                <th className="text-left px-5 py-3">#</th>
                <th className="text-left px-5 py-3">Vendedor</th>
                <th className="text-center px-5 py-3">Esta semana</th>
                <th className="text-center px-5 py-3">Racha</th>
                <th className="text-center px-5 py-3">XP Total</th>
                <th className="text-center px-5 py-3">Nivel</th>
                <th className="text-center px-5 py-3">Certificado</th>
                <th className="text-right px-5 py-3">Último acceso</th>
              </tr>
            </thead>
            <tbody>
              {team.map((member, i) => {
                const certEntry = certMap[member.user_id];
                const hasCert = certEntry?.certificate != null;

                return (
                  <tr key={member.user_id} className="border-b border-gray-800/50 hover:bg-surface-light/50 transition">
                    <td className="px-5 py-3 text-gray-500">{i + 1}</td>
                    <td className="px-5 py-3">
                      <div>
                        <span className="text-white font-medium">{member.full_name}</span>
                        <span className="text-gray-500 text-xs block">{member.email}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                        member.met_weekly_target
                          ? 'bg-green-500/10 text-green-400'
                          : member.lessons_this_week > 0
                            ? 'bg-amber-500/10 text-amber-400'
                            : 'bg-gray-700 text-gray-500'
                      }`}>
                        {member.lessons_this_week} lecciones
                      </span>
                    </td>
                    <td className="px-5 py-3 text-center">
                      {member.streak_current > 0 ? (
                        <span className="text-accent">🔥 {member.streak_current}d</span>
                      ) : (
                        <span className="text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-center text-white font-medium">
                      {member.total_xp.toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-center">
                      <span className="bg-primary/10 text-primary text-xs px-2 py-0.5 rounded-full">
                        Lvl {member.level}
                      </span>
                    </td>

                    {/* ── Certificado column ── */}
                    <td className="px-5 py-3 text-center">
                      {hasCert ? (
                        <div className="flex flex-col items-center gap-1">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400">
                            🏅 Emitido
                          </span>
                          <button
                            onClick={() => setSelectedCert({ full_name: member.full_name, certificate: certEntry.certificate })}
                            className="text-xs text-primary hover:underline"
                          >
                            Ver certificado
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
                          Pendiente
                        </span>
                      )}
                    </td>

                    <td className="px-5 py-3 text-right text-gray-500 text-xs">
                      {member.last_activity ? timeAgo(member.last_activity) : 'Nunca'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden divide-y divide-gray-800">
          {team.map((member) => {
            const certEntry = certMap[member.user_id];
            const hasCert = certEntry?.certificate != null;

            return (
              <div key={member.user_id} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-white font-medium">{member.full_name}</span>
                    <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      member.met_weekly_target
                        ? 'bg-green-500/10 text-green-400'
                        : member.lessons_this_week > 0
                          ? 'bg-amber-500/10 text-amber-400'
                          : 'bg-gray-700 text-gray-500'
                    }`}>
                      {member.lessons_this_week} esta semana
                    </span>
                  </div>
                  <span className="text-sm text-white font-medium">{member.total_xp} XP</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
                  {member.streak_current > 0 && <span>🔥 {member.streak_current}d racha</span>}
                  <span>Lvl {member.level}</span>
                  <span className="ml-auto">{member.last_activity ? timeAgo(member.last_activity) : 'Sin actividad'}</span>
                </div>
                {/* Mobile cert badge */}
                <div className="mt-2">
                  {hasCert ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full font-semibold">
                        🏅 Certificado emitido
                      </span>
                      <button
                        onClick={() => setSelectedCert({ full_name: member.full_name, certificate: certEntry.certificate })}
                        className="text-xs text-primary hover:underline"
                      >
                        Ver
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-600">Certificado: Pendiente</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {team.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No hay vendedores en esta empresa todavía.
          </div>
        )}
      </div>

      {/* Certificate modal */}
      {selectedCert && (
        <CertificateModal
          fullName={selectedCert.full_name}
          certificate={selectedCert.certificate}
          onClose={() => setSelectedCert(null)}
        />
      )}
    </div>
  );
}

/* ── Certificate modal ──────────────────────────────────────── */
function CertificateModal({ fullName, certificate, onClose }) {
  const earnedDate = new Date(certificate.earned_at);
  const formattedDate = earnedDate.toLocaleDateString('es-AR', {
    day: 'numeric', month: 'long', year: 'numeric',
  });

  const allModulesDone = certificate.modules.every((m) => m.completed);

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-surface rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="bg-gradient-to-r from-primary/20 to-emerald-500/20 border-b border-gray-800 px-6 py-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Certificado de habilitación</p>
              <h2 className="text-xl font-bold text-white">🏅 {certificate.badge_name}</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-white transition text-xl leading-none"
            >
              ×
            </button>
          </div>
        </div>

        {/* Modal body */}
        <div className="px-6 py-5 space-y-5">

          {/* Operario info */}
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-xl">
              👷
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Operario</p>
              <p className="text-white font-semibold text-lg">{fullName}</p>
            </div>
          </div>

          {/* Fecha de habilitación */}
          <div className="bg-surface-light rounded-xl px-4 py-3 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Fecha de habilitación</p>
              <p className="text-white font-medium">{formattedDate}</p>
            </div>
            <span className="text-2xl">📅</span>
          </div>

          {/* Módulos completados */}
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Módulos completados</p>
            <div className="space-y-2">
              {certificate.modules.map((mod, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between rounded-lg px-4 py-2.5 ${
                    mod.completed
                      ? 'bg-emerald-500/10 border border-emerald-500/20'
                      : 'bg-gray-800 border border-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={mod.completed ? 'text-emerald-400' : 'text-gray-500'}>
                      {mod.completed ? '✓' : '○'}
                    </span>
                    <span className={`text-sm font-medium ${mod.completed ? 'text-white' : 'text-gray-400'}`}>
                      {mod.title}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {mod.lessons_done}/{mod.total_lessons} lecciones
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Puntaje final */}
          <div className="bg-gradient-to-r from-primary/10 to-accent/10 border border-primary/20 rounded-xl px-4 py-3 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Puntaje final</p>
              <p className="text-2xl font-bold text-white">{certificate.total_xp.toLocaleString()} <span className="text-sm font-normal text-primary">XP</span></p>
            </div>
            <span className="text-3xl">⭐</span>
          </div>

          {/* Status */}
          <div className={`rounded-xl px-4 py-3 text-center ${allModulesDone ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-amber-500/10 border border-amber-500/20'}`}>
            <p className={`text-sm font-semibold ${allModulesDone ? 'text-emerald-400' : 'text-amber-400'}`}>
              {allModulesDone
                ? '✅ Habilitación completa — todos los módulos aprobados'
                : '⏳ Habilitación parcial — algunos módulos en progreso'}
            </p>
          </div>
        </div>

        {/* Modal footer */}
        <div className="px-6 pb-5">
          <button
            onClick={onClose}
            className="w-full bg-surface-light hover:bg-gray-700 text-white font-medium py-2.5 rounded-xl transition text-sm"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Helpers ─────────────────────────────────────────────────── */
function StatCard({ label, value, icon, color = '' }) {
  return (
    <div className="bg-surface rounded-xl p-4 text-center">
      <div className="text-2xl mb-1">{icon}</div>
      <div className={`text-2xl font-bold ${color || 'text-white'}`}>{value}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  );
}

function formatDate(isoString) {
  const d = new Date(isoString + 'T00:00:00');
  return d.toLocaleDateString('es-AR', { day: 'numeric', month: 'short' });
}

function timeAgo(isoString) {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `Hace ${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'Ayer';
  return `Hace ${days}d`;
}
