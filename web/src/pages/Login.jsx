import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token');

  return tokenFromUrl ? <VerifyToken token={tokenFromUrl} /> : <RequestLink />;
}

function RequestLink() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.requestLink(email, name);
      setSent(true);
    } catch (err) {
      setError(err.detail || 'Error al enviar el link');
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl p-8 max-w-md w-full text-center">
          <div className="text-5xl mb-4">📧</div>
          <h2 className="text-2xl font-bold mb-2">Revisá tu email</h2>
          <p className="text-gray-400">
            Te enviamos un magic link a <span className="text-primary font-medium">{email}</span>.
            Hacé click en el link para ingresar.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-1">
            <span className="text-primary">Sales</span>Leap
          </h1>
          <p className="text-gray-400">Capacitación gamificada para vendedores</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Nombre completo</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Tu nombre"
              required
              className="w-full bg-surface-light border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary transition"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@empresa.com"
              required
              className="w-full bg-surface-light border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary transition"
            />
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
          >
            {loading ? 'Enviando...' : 'Enviar magic link'}
          </button>
        </form>
      </div>
    </div>
  );
}

function VerifyToken({ token }) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [verifying, setVerifying] = useState(true);

  useState(() => {
    (async () => {
      try {
        const data = await api.verify(token);
        login(data.access_token);
        // Redirect based on onboarding status
        if (!data.onboarding_done) {
          navigate('/onboarding', { replace: true });
        } else {
          navigate('/dashboard', { replace: true });
        }
      } catch (err) {
        setError(err.detail || 'Token inválido o expirado');
        setVerifying(false);
      }
    })();
  });

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-surface rounded-2xl p-8 max-w-md w-full text-center">
          <div className="text-5xl mb-4">❌</div>
          <h2 className="text-xl font-bold mb-2">Error de verificación</h2>
          <p className="text-gray-400 mb-4">{error}</p>
          <a href="/login" className="text-primary hover:underline">Volver al login</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin text-4xl mb-4">⏳</div>
        <p className="text-gray-400">Verificando...</p>
      </div>
    </div>
  );
}
