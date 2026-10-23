import { useState, useEffect } from 'react';
import api from '../lib/api';

const PERFIS = ['ADMINISTRADOR', 'GESTOR', 'OPERADOR'];

export default function AdminApp({ user, onLogout }) {
  const [tab, setTab] = useState('usuarios');

  const podeUsuarios = ['ADMINISTRADOR', 'GESTOR'].includes(user.perfil);

  return (
    <div className="admin-wrap">
      <header className="admin-header">
        <div>
          <strong>Atualiza SUS — Painel</strong>
          <span className="admin-user">{user.nome} · {user.perfil}</span>
        </div>
        <button className="btn-secundario" onClick={onLogout}>Sair</button>
      </header>

      <nav className="admin-tabs">
        {podeUsuarios && (
          <button className={tab === 'usuarios' ? 'ativo' : ''} onClick={() => setTab('usuarios')}>
            Usuários
          </button>
        )}
        <button className={tab === 'senha' ? 'ativo' : ''} onClick={() => setTab('senha')}>
          Minha Senha
        </button>
        {podeUsuarios && (
          <button className={tab === 'logs' ? 'ativo' : ''} onClick={() => setTab('logs')}>
            Logs
          </button>
        )}
      </nav>

      <main className="admin-body">
        {tab === 'usuarios' && podeUsuarios && <UsuariosTab user={user} />}
        {tab === 'senha' && <SenhaTab />}
        {tab === 'logs' && podeUsuarios && <LogsTab />}
      </main>
    </div>
  );
}

/* ============================================================
   ABA: USUÁRIOS
   ============================================================ */
function UsuariosTab({ user }) {
  const [lista, setLista] = useState([]);
  const [form, setForm] = useState({ nome: '', login: '', perfil: 'OPERADOR' });
  const [msg, setMsg] = useState('');

  const carregar = async () => {
    const { data } = await api.get('/usuarios');
    setLista(data);
  };
  useEffect(() => { carregar(); }, []);

  const criar = async (e) => {
    e.preventDefault();
    setMsg('');
    try {
      await api.post('/usuarios', form);
      setForm({ nome: '', login: '', perfil: 'OPERADOR' });
      await carregar();
      setMsg('Usuário criado com senha padrão "123".');
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Erro ao criar usuário');
    }
  };

  const alternarAtivo = async (u) => {
    await api.patch(`/usuarios/${u.id}`, { ativo: !u.ativo });
    await carregar();
  };

  const mudarPerfil = async (u, perfil) => {
    try {
      await api.patch(`/usuarios/${u.id}`, { perfil });
      await carregar();
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Erro ao alterar perfil');
    }
  };

  // perfis que o usuário logado pode escolher ao criar
  const perfisPermitidos = PERFIS.filter(
    p => user.perfil === 'ADMINISTRADOR' || p !== 'ADMINISTRADOR'
  );

  return (
    <div>
      <h2>Usuários</h2>

      <form className="admin-form" onSubmit={criar}>
        <input
          placeholder="Nome completo"
          value={form.nome}
          onChange={e => setForm({ ...form, nome: e.target.value })}
          required
        />
        <input
          placeholder="Login"
          value={form.login}
          onChange={e => setForm({ ...form, login: e.target.value })}
          required
        />
        <select
          value={form.perfil}
          onChange={e => setForm({ ...form, perfil: e.target.value })}
        >
          {perfisPermitidos.map(p => <option key={p}>{p}</option>)}
        </select>
        <button className="btn-primario" type="submit">Criar (senha 123)</button>
      </form>

      {msg && <div className="admin-msg">{msg}</div>}

      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th><th>Nome</th><th>Login</th>
            <th>Perfil</th><th>Ativo</th><th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {lista.map(u => {
            const ehAdmin = u.perfil === 'ADMINISTRADOR';
            const bloqueado = ehAdmin && user.perfil === 'GESTOR';

            return (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.nome}</td>
                <td>{u.login}</td>
                <td>
                  <select
                    value={u.perfil}
                    disabled={u.id === user.id || bloqueado}
                    onChange={e => mudarPerfil(u, e.target.value)}
                  >
                    {PERFIS.map(p => <option key={p}>{p}</option>)}
                  </select>
                </td>
                <td>{u.ativo ? 'Sim' : 'Não'}</td>
                <td>
                  <button
                    className="btn-secundario"
                    onClick={() => alternarAtivo(u)}
                    disabled={u.id === user.id || bloqueado}
                  >
                    {u.ativo ? 'Desativar' : 'Ativar'}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ============================================================
   ABA: MINHA SENHA (todos os perfis)
   ============================================================ */
function SenhaTab() {
  const [atual, setAtual] = useState('');
  const [nova, setNova] = useState('');
  const [msg, setMsg] = useState('');

  const salvar = async (e) => {
    e.preventDefault();
    setMsg('');
    try {
      await api.post('/usuarios/me/senha', {
        senha_atual: atual || null,
        senha_nova: nova,
      });
      setMsg('Senha alterada com sucesso.');
      setAtual(''); setNova('');
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Erro ao alterar senha');
    }
  };

  return (
    <div>
      <h2>Minha Senha</h2>
      <form className="admin-form-vertical" onSubmit={salvar}>
        <label>
          Senha atual <small>(deixe em branco se ainda for a padrão "123")</small>
        </label>
        <input
          type="password"
          value={atual}
          onChange={e => setAtual(e.target.value)}
        />
        <label>Nova senha</label>
        <input
          type="password"
          value={nova}
          onChange={e => setNova(e.target.value)}
          required
        />
        <button className="btn-primario" type="submit">Alterar</button>
      </form>
      {msg && <div className="admin-msg">{msg}</div>}
    </div>
  );
}

/* ============================================================
   ABA: LOGS
   ============================================================ */
function LogsTab() {
  const [logs, setLogs] = useState([]);
  useEffect(() => {
    api.get('/logs').then(r => setLogs(r.data)).catch(() => {});
  }, []);

  return (
    <div>
      <h2>Logs</h2>
      <table className="admin-table">
        <thead>
          <tr><th>Data</th><th>Usuário</th><th>Ação</th><th>Descrição</th></tr>
        </thead>
        <tbody>
          {logs.map(l => (
            <tr key={l.id}>
              <td>{new Date(l.data_hora).toLocaleString('pt-BR')}</td>
              <td>{l.usuario_id ?? '—'}</td>
              <td>{l.acao}</td>
              <td>{l.descricao}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}