import { useState } from 'react';
import api from '../lib/api';

export default function Login({ onLogin }) {
  const [login, setLogin] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErro(''); setLoading(true);
    try {
      const { data } = await api.post('/auth/login', { login, senha });
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(data));
      onLogin(data);
    } catch (err) {
      setErro(err.response?.data?.detail || 'Falha ao entrar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrap">
      <form className="login-box" onSubmit={submit}>
        <h2>Painel Administrativo</h2>
        <p className="login-sub">Atualiza SUS</p>
        {erro && <div className="totem-erro">{erro}</div>}

        <label>Login</label>
        <input value={login} onChange={e => setLogin(e.target.value)} autoFocus />

        <label>Senha</label>
        <input type="password" value={senha} onChange={e => setSenha(e.target.value)} />

        <button type="submit" className="btn-primario" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}