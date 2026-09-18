import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'
import logoPrefeitura from './img/logo-prefeitura.png'

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL

/* ============================================================
   HELPERS
   ============================================================ */
const apenasDigitos = (v) => String(v || '').replace(/\D/g, '');

const formatarCPF = (v) => {
  const nums = apenasDigitos(v).slice(0, 11);
  let out = '';
  for (let i = 0; i < nums.length; i++) {
    if (i === 3 || i === 6) out += '.';
    if (i === 9) out += '-';
    out += nums[i];
  }
  return out;
};

const formatarData = (v) => {
  if (!v) return '—';
  const s = String(v).replace('Z', '');
  const d = new Date(s);
  if (isNaN(d.getTime())) return s;
  return d.toLocaleDateString('pt-BR');
};

const formatarTelefone = (num) => {
  const n = apenasDigitos(num);
  if (n.length === 11) return `(${n.slice(0,2)}) ${n.slice(2,7)}-${n.slice(7)}`;
  if (n.length === 10) return `(${n.slice(0,2)}) ${n.slice(2,6)}-${n.slice(6)}`;
  return num;
};

/* ============================================================
   ÍCONES
   ============================================================ */
const IconePessoaOk = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="10" cy="8" r="3.5" />
    <path d="M4 20c0-3.3 2.7-6 6-6" />
    <polyline points="14.5 15.5 16.5 17.5 20.5 13.5" />
  </svg>
);

const IconeBancoDados = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="8" ry="2.5" />
    <path d="M4 5v6c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5V5" />
    <path d="M4 11v6c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5v-6" />
  </svg>
);

const IconeEscudoOk = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5l-8-3z" />
    <polyline points="8.5 12 11 14.5 16 9.5" />
  </svg>
);

const IconeLupa = ({ size = 36 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="7" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const IconeCheck = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="4 12 10 18 20 6" />
  </svg>
);

const IconeApagar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z" />
    <line x1="18" y1="9" x2="12" y2="15" />
    <line x1="12" y1="9" x2="18" y2="15" />
  </svg>
);

const IconeSpinner = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" className="giro">
    <path d="M21 12a9 9 0 1 1-6.22-8.56" />
  </svg>
);

const IconeCasa = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 9.5V21h14V9.5" />
  </svg>
);

const IconeTelefone = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7 12.8 12.8 0 0 0 .7 2.8 2 2 0 0 1-.4 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4 12.8 12.8 0 0 0 2.8.7 2 2 0 0 1 1.7 2z" />
  </svg>
);

const IconeCracha = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="16" rx="2" />
    <circle cx="9" cy="10" r="2.5" />
    <path d="M5 18c0-2.2 1.8-4 4-4s4 1.8 4 4" />
    <line x1="15" y1="9" x2="19" y2="9" />
    <line x1="15" y1="13" x2="19" y2="13" />
  </svg>
);

/* ============================================================
   COMPONENTE PRINCIPAL
   ============================================================ */
export default function AtualizaSUS() {
  const [tela, setTela] = useState('welcome');
  const [cpf, setCpf] = useState('');
  const [nomeMae, setNomeMae] = useState('');
  const [erro, setErro] = useState('');
  const [dados, setDados] = useState(null); // objeto único do backend

  const [progresso, setProgresso] = useState(0);
  const [sistemas, setSistemas] = useState({ esus: 'pendente', sisreg: 'pendente', consulfarma: 'pendente' });
  const [contador, setContador] = useState(14);
  const timersRef = useRef([]);

  const limparTimers = () => {
    timersRef.current.forEach(t => clearTimeout(t));
    timersRef.current = [];
  };

  const resetarTudo = () => {
    limparTimers();
    setCpf(''); setNomeMae(''); setErro(''); setDados(null);
    setProgresso(0);
    setSistemas({ esus: 'pendente', sisreg: 'pendente', consulfarma: 'pendente' });
  };

  const irParaWelcome = () => { resetarTudo(); setTela('welcome'); };

  /* -------- Contagem regressiva telas finais -------- */
  useEffect(() => {
    if (tela !== 'tudo-ok' && tela !== 'precisa-atualizar') return;
    setContador(14);
    const int = setInterval(() => {
      setContador(c => {
        if (c <= 1) { clearInterval(int); irParaWelcome(); return 14; }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(int);
  }, [tela]);

  /* -------- Teclados -------- */
  const teclarNumero = (n) => {
    if (cpf.length >= 11) return;
    setErro('');
    setCpf(prev => prev + n);
  };
  const apagarNumero = () => setCpf(prev => prev.slice(0, -1));

  const teclarLetra = (l) => {
    setErro('');
    setNomeMae(prev => (prev + l).slice(0, 30));
  };
  const apagarLetra = () => setNomeMae(prev => prev.slice(0, -1));

  /* -------- Fluxo -------- */
  const confirmarCPF = () => {
    if (cpf.length !== 11) { setErro('Digite os 11 dígitos do CPF.'); return; }
    setErro('');
    setTela('mae');
  };

  const confirmarMae = async () => {
    if (!nomeMae.trim()) { setErro('Digite o primeiro nome da mãe.'); return; }
    setErro('');
    setTela('loading');
    setProgresso(5);
    setSistemas({ esus: 'carregando', sisreg: 'pendente', consulfarma: 'pendente' });

    timersRef.current.push(setTimeout(() => {
      setProgresso(35);
      setSistemas({ esus: 'ok', sisreg: 'carregando', consulfarma: 'pendente' });
    }, 700));
    timersRef.current.push(setTimeout(() => {
      setProgresso(65);
      setSistemas({ esus: 'ok', sisreg: 'ok', consulfarma: 'carregando' });
    }, 1500));
    timersRef.current.push(setTimeout(() => {
      setProgresso(95);
      setSistemas({ esus: 'ok', sisreg: 'ok', consulfarma: 'ok' });
    }, 2300));

    try {
      const res = await axios.get(`${API_BASE_URL}/consulta/${cpf}`, {
        params: { nome_mae: nomeMae.trim() },
        timeout: 15000
      });

      setDados(res.data);

      timersRef.current.push(setTimeout(() => {
        setProgresso(100);
        setTela('verificacao');
      }, 2800));

    } catch (e) {
      limparTimers();
      if (e.response?.status === 403) {
        setErro('Nome da mãe incorreto. Verifique e tente novamente.');
        setTela('mae');
      } else if (e.response?.status === 404) {
        setErro('Nenhum cadastro encontrado para este CPF.');
        setTela('cpf');
      } else if (e.code === 'ECONNABORTED') {
        setErro('O sistema demorou para responder. Tente novamente.');
        setTela('mae');
      } else {
        setErro('Não foi possível verificar seus dados agora. Tente novamente.');
        setTela('mae');
      }
    }
  };

  /* ============================================================
     RENDER
     ============================================================ */
  return (
    <div className="totem-atualiza">
      {tela !== 'welcome' && tela !== 'cpf' && tela !== 'mae' && (
        <header className="totem-header">
          <div className="totem-header-brand">
            <strong>Atualiza SUS</strong>
          </div>
          <div className="totem-header-data">
            {new Date().toLocaleDateString('pt-BR')} &nbsp;•&nbsp;
            {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </div>
        </header>
      )}

      <main className="totem-body">
        {/* ===================== WELCOME ===================== */}
        {tela === 'welcome' && (
          <div className="tela tela-welcome">
            <h1 className="welcome-nome-software">ATUALIZA SUS</h1>
            <div className="logo">
              <img src={logoPrefeitura} alt="Prefeitura" />
            </div>
            <h1 className="welcome-titulo">Bem-vindo(a) ao Totem de<br /> Atualização Cadastral</h1>
            <p className="welcome-sub">
              Mantenha seus dados do SUS sempre atualizados para garantir
              agilidade em suas consultas e exames.
            </p>

            <div className="welcome-cards">
              <div className="welcome-card">
                <div className="wc-icon"><IconePessoaOk /></div>
                <span>Identificação rápida</span>
              </div>
              <div className="welcome-card">
                <div className="wc-icon"><IconeBancoDados /></div>
                <span>Histórico integrado</span>
              </div>
              <div className="welcome-card">
                <div className="wc-icon"><IconeEscudoOk /></div>
                <span>Segurança de dados</span>
              </div>
            </div>

            <button className="btn-primario-grande" onClick={() => setTela('cpf')}>
              Verificar meu cadastro →
            </button>
          </div>
        )}

        {/* ===================== CPF ===================== */}
        {tela === 'cpf' && (
          <div className="tela tela-cpf">
            <div className="logo">
              <img src={logoPrefeitura} alt="Prefeitura" />
            </div>
            <h2 className="tela-titulo">Informe seu CPF</h2>
            <p className="tela-sub">Utilize o teclado abaixo para digitar os números do seu documento.</p>

            <div className={`cpf-display ${cpf ? 'preenchido' : ''}`}>
              {cpf ? formatarCPF(cpf) : '000.000.000-00'}
            </div>

            {erro && <div className="totem-erro">{erro}</div>}

            <div className="teclado-numerico">
              {[1,2,3,4,5,6,7,8,9].map(n => (
                <button key={n} className="tecla" onClick={() => teclarNumero(String(n))}>{n}</button>
              ))}
              <button className="tecla tecla-vazia" disabled />
              <button className="tecla" onClick={() => teclarNumero('0')}>0</button>
              <button className="tecla tecla-apagar" onClick={apagarNumero} aria-label="Apagar">
                <IconeApagar />
              </button>
            </div>

            <button
              className="btn-primario-grande"
              onClick={confirmarCPF}
              disabled={cpf.length !== 11}
            >
              Confirmar Documento
            </button>

            <button className="btn-texto-voltar" onClick={irParaWelcome}>← Voltar</button>

            <p className="lgpd-aviso">
              Seus dados estão protegidos de acordo com a LGPD.
            </p>
          </div>
        )}

        {/* ===================== NOME DA MÃE ===================== */}
        {tela === 'mae' && (
          <div className="tela tela-mae">
            <div className="logo">
              <img src={logoPrefeitura} alt="Prefeitura" />
            </div>
            <h2 className="tela-titulo">Confirme sua Identidade</h2>
            <p className="tela-sub">
              Para garantir a segurança dos seus dados, informe o primeiro
              nome da sua mãe conforme registrado no cartão SUS.
            </p>

            <div className={`mae-display ${nomeMae ? 'preenchido' : ''}`}>
              {nomeMae || 'Ex: MARIA'}
            </div>

            {erro && <div className="totem-erro">{erro}</div>}

            <div className="teclado-letras">
              {['Q','W','E','R','T','Y','U','I','O','P'].map(l => (
                <button key={l} className="tecla" onClick={() => teclarLetra(l)}>{l}</button>
              ))}
              {['A','S','D','F','G','H','J','K','L','Ç'].map(l => (
                <button key={l} className="tecla" onClick={() => teclarLetra(l)}>{l}</button>
              ))}
              {['Z','X','C','V','B','N','M'].map(l => (
                <button key={l} className="tecla" onClick={() => teclarLetra(l)}>{l}</button>
              ))}
            </div>

            <div className="teclado-acoes">
              <button className="tecla tecla-larga" onClick={() => teclarLetra(' ')}>
                ESPAÇO
              </button>
              <button className="tecla tecla-larga tecla-apagar" onClick={apagarLetra}>
                <IconeApagar /> APAGAR
              </button>
            </div>

            <div className="linha-botoes">
              <button className="btn-secundario" onClick={irParaWelcome}>CANCELAR</button>
              <button className="btn-primario" onClick={confirmarMae} disabled={!nomeMae.trim()}>
                CONFIRMAR
              </button>
            </div>
          </div>
        )}

        {/* ===================== LOADING ===================== */}
        {tela === 'loading' && (
          <div className="tela tela-loading">
            <div className="loading-icone"><IconeLupa size={42} /></div>
            <h2 className="tela-titulo">Buscando seus dados</h2>
            <p className="tela-sub">
              Estamos integrando as informações dos sistemas de saúde
              para verificar sua situação cadastral.
            </p>

            <div className="progresso-wrap">
              <div className="progresso-header">
                <span>PROCESSANDO VERIFICAÇÃO</span>
                <strong>{progresso}%</strong>
              </div>
              <div className="progresso-barra">
                <div className="progresso-preenchida" style={{ width: `${progresso}%` }} />
              </div>
              <div className="progresso-status">🔄 Sincronizando com a base municipal...</div>
            </div>

            <div className="sistemas-lista">
              <SistemaItem nome="E-SUS Três Lagoas" status={sistemas.esus} />
              <SistemaItem nome="SISREG (Sistema de Regulação)" status={sistemas.sisreg} />
              <SistemaItem nome="Consulfarma Integração" status={sistemas.consulfarma} />
            </div>

            <div className="lgpd-box">
              <span>🛡️</span>
              <p>Seus dados são criptografados e acessados apenas para fins de verificação administrativa de saúde pública.</p>
            </div>

            <button className="btn-texto-voltar" onClick={irParaWelcome}>✕ Cancelar Operação</button>
          </div>
        )}

        {/* ===================== VERIFICAÇÃO ===================== */}
        {tela === 'verificacao' && dados && (
          <div className="tela tela-verificacao">
            <h2 className="tela-titulo">Confirme seus dados cadastrais</h2>
            <p className="tela-sub">
              Verifique se as informações abaixo estão corretas. Caso algo esteja
              desatualizado, você poderá solicitar a correção ao final.
            </p>

            <div className="verificacao-cards">
              <VerificacaoCard titulo="Dados pessoais" icone={<IconeCracha />} itens={[
                { label: 'Nome completo', valor: dados.nome || '—' },
                { label: 'CPF', valor: formatarCPF(dados.cpf) },
                { label: 'Data de nascimento', valor: formatarData(dados.data_nascimento) },
                { label: 'Nome da mãe', valor: dados.nome_mae || '—' },
              ]}/>

              <VerificacaoCard titulo="Endereço" icone={<IconeCasa />} itens={[
                { label: 'Endereço completo', valor: dados.endereco_completo || 'Não informado' },
              ]}/>

              <VerificacaoCard titulo="Telefones" icone={<IconeTelefone />} itens={
                (dados.telefones && dados.telefones.length && dados.telefones[0] !== 'Não informado')
                  ? dados.telefones.map(t => ({ label: 'Telefone', valor: formatarTelefone(t) }))
                  : [{ label: 'Telefone', valor: 'Não informado' }]
              }/>
            </div>

            <div className="linha-botoes">
              <button className="btn-secundario" onClick={() => setTela('tudo-ok')}>
                Meu cadastro está correto
              </button>
              <button className="btn-primario" onClick={() => setTela('precisa-atualizar')}>
                Preciso atualizar
              </button>
            </div>
          </div>
        )}

        {/* ===================== PRECISA ATUALIZAR ===================== */}
        {tela === 'precisa-atualizar' && (
          <div className="tela tela-final">
            <div className="final-icone alerta">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <h2 className="tela-titulo">Atualização Necessária</h2>
            <div className="aviso-dirija">
              DIRIJA-SE À: <strong>Sala de Atualização</strong> (Sala X - ao lado)
            </div>
            <p className="tela-sub">
              Apresente seu CPF e um documento com foto ao atendente.
            </p>
            <div className="contador-final">Retornando à tela inicial em {contador}s</div>
            <button className="btn-secundario" onClick={irParaWelcome}>Voltar ao início</button>
          </div>
        )}

        {/* ===================== TUDO OK ===================== */}
        {tela === 'tudo-ok' && (
          <div className="tela tela-final">
            <div className="final-icone sucesso"><IconeCheck /></div>
            <h2 className="tela-titulo">Tudo OK! Que ótimo que seu cadastro está atualizado</h2>
            <p className="tela-sub">
              Obrigado por colaborar com a saúde pública de Três Lagoas.
            </p>
            <div className="contador-final">Retornando à tela inicial em {contador}s</div>
            <button className="btn-secundario" onClick={irParaWelcome}>Voltar ao início</button>
          </div>
        )}
      </main>
    </div>
  );
}

/* ============================================================
   SUBCOMPONENTES
   ============================================================ */
function SistemaItem({ nome, status }) {
  return (
    <div className={`sistema-item status-${status}`}>
      <div className="sistema-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="12" cy="6" rx="7" ry="2.5" />
          <path d="M5 6v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6" />
          <path d="M5 12v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6" />
        </svg>
      </div>
      <div className="sistema-info">
        <strong>{nome}</strong>
        <span>
          {status === 'pendente' && 'Aguardando...'}
          {status === 'carregando' && 'Consultando registros...'}
          {status === 'ok' && 'Consulta concluída'}
        </span>
      </div>
      <div className="sistema-status">
        {status === 'carregando' && <span className="mini-spin"><IconeSpinner /></span>}
        {status === 'ok' && <span className="check-ok"><IconeCheck /></span>}
      </div>
    </div>
  );
}

function VerificacaoCard({ titulo, itens, icone }) {
  return (
    <div className="verificacao-card">
      <div className="vc-header">
        <span className="vc-badge">
          {icone || <IconeCheck />}
        </span>
        <strong>{titulo}</strong>
      </div>
      <ul>
        {itens.map((item, i) => (
          <li key={i}>
            <span className="vc-label">{item.label}</span>
            <span className="vc-valor">{item.valor}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}