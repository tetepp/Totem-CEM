CREATE DATABASE totem_sus;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    login VARCHAR(100) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil VARCHAR(20) NOT NULL DEFAULT 'OPERADOR',
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_usuario_perfil CHECK (perfil IN ('ADMINISTRADOR', 'GESTOR', 'OPERADOR'))
);

CREATE TABLE totens (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    identificacao VARCHAR(100) NOT NULL UNIQUE,
    descricao VARCHAR(255),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE configuracao_totem (
    id SERIAL PRIMARY KEY,
    totem_id INTEGER NOT NULL UNIQUE,
    sala_redirecionamento VARCHAR(100) NOT NULL,
    mensagem_atualizado TEXT NOT NULL,
    mensagem_nao_atualizado TEXT NOT NULL,
    atualizado_por INTEGER,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_config_totem FOREIGN KEY (totem_id) REFERENCES totens(id) ON DELETE CASCADE,
    CONSTRAINT fk_config_usuario FOREIGN KEY (atualizado_por) REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE TABLE sessoes_totem(
    id BIGSERIAL PRIMARY KEY,
    sessao_uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    totem_id INTEGER NOT NULL,
    iniciada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada_em TIMESTAMP,
    clicou_verificar BOOLEAN NOT NULL DEFAULT FALSE,
    resultado VARCHAR(30),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sessao_totem FOREIGN KEY (totem_id) REFERENCES totens(id) ON DELETE RESTRICT,
    CONSTRAINT chk_resultado_sessao CHECK(resultado IS NULL OR resultado IN ('ATUALIZADO', 'NAO_ATUALIZADO', 'ABANDONOU')),
    CONSTRAINT chk_finalizacao CHECK (finalizada_em IS NULL OR finalizada_em >= iniciada_em)
);

CREATE TABLE logs(
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER,
    acao VARCHAR(100) NOT NULL,
    descricao TEXT,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_log_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX idx_sessoes_totem_data ON sessoes_totem (iniciado_em);
CREATE INDEX idx_sessoes_totem_resultado ON sessoes_totem (resultado);
CREATE INDEX idx_sessoes_totem_totem ON sessoes_totem (totem_id);
CREATE INDEX idx_logs_data ON logs (data_hora);
CREATE INDEX idx_logs_usuario ON logs (usuario_id);