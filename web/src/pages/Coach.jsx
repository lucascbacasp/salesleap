import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

// ── Configuración de UI por industry (espejea INDUSTRY_COACH_CONFIG del backend) ──
const COACH_UI_CONFIG = {
  onboarding_alimentaria: {
    title: 'Coach de Inocuidad Alimentaria',
    welcome: (name) =>
      `¡Hola ${name}! 👋 Soy tu Coach de Inocuidad Alimentaria. Podés preguntarme sobre BPM, CCPs, HACCP, trazabilidad, alérgenos o cualquier tema de tu capacitación. ¿En qué te puedo ayudar?`,
    prompts: [
      '¿Qué es un Punto Crítico de Control (CCP)?',
      '¿Cuáles son las BPM que debo cumplir en planta?',
      'Explicame el sistema HACCP',
      '¿Cómo gestiono alérgenos en la línea de producción?',
    ],
  },
  alimentaria: {
    title: 'Coach de Inocuidad Alimentaria',
    welcome: (name) =>
      `¡Hola ${name}! 👋 Soy tu Coach de Inocuidad Alimentaria. Podés preguntarme sobre BPM, CCPs, HACCP, trazabilidad, alérgenos o cualquier tema de tu capacitación. ¿En qué te puedo ayudar?`,
    prompts: [
      '¿Qué es un Punto Crítico de Control (CCP)?',
      '¿Cuáles son las BPM que debo cumplir en planta?',
      'Explicame el sistema HACCP',
      '¿Cómo gestiono alérgenos en la línea de producción?',
    ],
  },
  auto: {
    title: 'Coach de Ventas Automotrices',
    welcome: (name) =>
      `¡Hola ${name}! 👋 Soy tu Coach de Ventas Automotrices. Podés preguntarme sobre venta consultiva, manejo de objeciones, cierre, posventa o practicar un roleplay. ¿En qué te puedo ayudar?`,
    prompts: [
      '¿Cómo manejo la objeción "es muy caro"?',
      'Dame tips para cerrar una venta hoy',
      'Quiero practicar un roleplay de venta de autos',
      '¿Cómo hago un buen seguimiento de leads automotriz?',
    ],
  },
  inmobiliaria: {
    title: 'Coach de Ventas Inmobiliarias',
    welcome: (name) =>
      `¡Hola ${name}! 👋 Soy tu Coach de Ventas Inmobiliarias. Podés preguntarme sobre captación, tasación, negociación, cierre de escrituras o practicar un roleplay. ¿En qué te puedo ayudar?`,
    prompts: [
      '¿Cómo capto propiedades en exclusiva?',
      'Dame tips para cerrar una escritura',
      '¿Cómo argumento el precio de tasación?',
      '¿Cómo manejo la objeción del precio de una propiedad?',
    ],
  },
  _default: {
    title: 'SalesLeap Coach',
    welcome: (name) =>
      `¡Hola ${name}! 👋 Soy tu SalesLeap Coach. Podés preguntarme sobre ventas, técnicas de cierre, manejo de objeciones, o practicar un roleplay. ¿En qué te puedo ayudar?`,
    prompts: [
      '¿Cómo manejo la objeción "es muy caro"?',
      'Dame tips para cerrar una venta hoy',
      'Quiero practicar un roleplay de ventas',
      '¿Cómo hago un buen seguimiento de leads?',
    ],
  },
};

export default function Coach() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const firstName = user?.full_name?.split(' ')[0] || '';
  const config = COACH_UI_CONFIG[user?.industry] || COACH_UI_CONFIG._default;

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: config.welcome(firstName),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch('/api/coach/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          message: text,
          conversation_history: history,
        }),
      });

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response || data.detail || 'No pude responder.' },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '❌ Error de conexión. Intentá de nuevo.' },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickPrompts = config.prompts;

  return (
    <div className="min-h-screen flex flex-col max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')} className="text-gray-400 hover:text-white transition">
            ←
          </button>
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-xl">
            🧠
          </div>
          <div>
            <h1 className="font-semibold text-white">{config.title}</h1>
            <p className="text-xs text-green-400">En línea</p>
          </div>
        </div>
        <div className="text-xs text-gray-500">
          {user?.industry || 'General'} · Nivel {user?.level || 1}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-primary text-white rounded-br-sm'
                  : 'bg-surface text-gray-300 rounded-bl-sm'
              }`}
            >
              {msg.content.split('\n').map((line, j) => (
                <p key={j} className={`${j > 0 ? 'mt-2' : ''} text-sm leading-relaxed`}>
                  {line}
                </p>
              ))}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEnd} />
      </div>

      {/* Quick prompts (show only when no user messages yet) */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2">
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt, i) => (
              <button
                key={i}
                onClick={() => {
                  setInput(prompt);
                  inputRef.current?.focus();
                }}
                className="text-xs bg-surface border border-gray-700 text-gray-400 hover:text-white hover:border-primary px-3 py-1.5 rounded-full transition"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribí tu pregunta..."
            rows={1}
            className="flex-1 bg-surface border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-primary transition resize-none"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="bg-primary hover:bg-primary-dark text-white px-4 rounded-xl transition disabled:opacity-50"
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}
