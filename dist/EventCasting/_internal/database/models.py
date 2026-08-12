CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE NOT NULL,
    data_nascimento TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    whatsapp TEXT NOT NULL,
    cidade TEXT NOT NULL,
    estado TEXT NOT NULL,
    foto TEXT,
    funcao_principal TEXT NOT NULL,
    experiencia TEXT,
    chave_pix TEXT,
    perfil TEXT NOT NULL DEFAULT 'STAFF',
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT NOT NULL,
    hora_inicio TEXT NOT NULL,
    hora_fim TEXT NOT NULL,
    local TEXT NOT NULL,
    endereco TEXT NOT NULL,
    cidade TEXT NOT NULL,
    estado TEXT NOT NULL,
    observacoes TEXT,
    status TEXT NOT NULL DEFAULT 'RASCUNHO',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vagas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    funcao TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    valor_diaria REAL NOT NULL,
    quantidade_dias INTEGER DEFAULT 1,
    horario_inicio TEXT NOT NULL,
    horario_fim TEXT NOT NULL,
    descricao TEXT,
    status TEXT NOT NULL DEFAULT 'ABERTA',
    FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS candidaturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaga_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    data_candidatura DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vaga_id) REFERENCES vagas (id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    UNIQUE(vaga_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS escalas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    vaga_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ESCALADO',
    confirmado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE,
    FOREIGN KEY (vaga_id) REFERENCES vagas (id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS presencas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escala_id INTEGER NOT NULL,
    checkin DATETIME,
    checkout DATETIME,
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    FOREIGN KEY (escala_id) REFERENCES escalas (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    evento_id INTEGER NOT NULL,
    valor REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    data_pagamento DATETIME,
    observacao TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS avaliacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    avaliador_id INTEGER NOT NULL,
    avaliado_id INTEGER NOT NULL,
    nota REAL NOT NULL,
    pontualidade REAL NOT NULL,
    profissionalismo REAL NOT NULL,
    desempenho REAL NOT NULL,
    comentario TEXT,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE,
    FOREIGN KEY (avaliador_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    FOREIGN KEY (avaliado_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notificacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'INFO',
    lida INTEGER DEFAULT 0,
    criada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dias_bloqueados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    motivo TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    UNIQUE(usuario_id, data)
);
"""
