CREATE DATABASE totem_sus;
\c totem_sus;

CREATE TABLE respostas_cadastro (
    id              BIGSERIAL PRIMARY KEY,
    nome_paciente   VARCHAR(200) NOT NULL,
    cadastro_correto    BOOLEAN NOT NULL DEFAULT FALSE,
    precisa_atualizar   BOOLEAN NOT NULL DEFAULT FALSE,
    data_hora       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_uma_escolha CHECK (
        (cadastro_correto = TRUE  AND precisa_atualizar = FALSE) OR
        (cadastro_correto = FALSE AND precisa_atualizar = TRUE)
    )
);