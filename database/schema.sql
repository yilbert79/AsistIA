-- Esquema MySQL compatible con los modelos ORM de backend/app/models.py
CREATE DATABASE IF NOT EXISTS asistia_teinco_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asistia_teinco_db;

CREATE TABLE IF NOT EXISTS dependencias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  contact_email VARCHAR(180) NOT NULL DEFAULT '',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  context TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS usuarios_admin (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(180) NOT NULL UNIQUE,
  full_name VARCHAR(140) NOT NULL,
  password_hash VARCHAR(180) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'DIVISION_AGENT',
  department_id INT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (department_id) REFERENCES dependencias(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS conversaciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  session_code VARCHAR(64) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contactos_usuario (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(140) NULL,
  email VARCHAR(180) NULL,
  phone VARCHAR(40) NULL,
  consent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS mensajes_chat (
  id INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id INT NOT NULL,
  contact_id INT NULL,
  department_id INT NOT NULL,
  question TEXT NOT NULL,
  topic VARCHAR(120) NOT NULL DEFAULT 'general',
  ai_answer TEXT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'PROCESSING',
  public_token_hash CHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_mensajes_chat_conversation_id (conversation_id),
  INDEX ix_mensajes_chat_department_id (department_id),
  INDEX ix_mensajes_chat_status (status),
  INDEX ix_mensajes_chat_topic (topic),
  INDEX ix_mensajes_chat_created_at (created_at),
  FOREIGN KEY (conversation_id) REFERENCES conversaciones(id) ON DELETE CASCADE,
  FOREIGN KEY (contact_id) REFERENCES contactos_usuario(id) ON DELETE SET NULL,
  FOREIGN KEY (department_id) REFERENCES dependencias(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS respuestas_division (
  id INT AUTO_INCREMENT PRIMARY KEY,
  message_id INT NOT NULL,
  author_id INT NOT NULL,
  answer TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_respuestas_division_message_id (message_id),
  FOREIGN KEY (message_id) REFERENCES mensajes_chat(id) ON DELETE CASCADE,
  FOREIGN KEY (author_id) REFERENCES usuarios_admin(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS validaciones_lider (
  id INT AUTO_INCREMENT PRIMARY KEY,
  message_id INT NOT NULL,
  validator_id INT NOT NULL,
  decision VARCHAR(24) NOT NULL,
  corrected_answer TEXT NULL,
  comment TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_validaciones_lider_message_id (message_id),
  FOREIGN KEY (message_id) REFERENCES mensajes_chat(id) ON DELETE CASCADE,
  FOREIGN KEY (validator_id) REFERENCES usuarios_admin(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS base_conocimiento (
  id INT AUTO_INCREMENT PRIMARY KEY,
  department_id INT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  source VARCHAR(240) NOT NULL DEFAULT '',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  approved_by INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_base_conocimiento_department_id (department_id),
  FOREIGN KEY (department_id) REFERENCES dependencias(id) ON DELETE SET NULL,
  FOREIGN KEY (approved_by) REFERENCES usuarios_admin(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notificaciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  message_id INT NOT NULL,
  channel VARCHAR(24) NOT NULL,
  recipient VARCHAR(180) NULL,
  status VARCHAR(24) NOT NULL DEFAULT 'PENDING',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_notificaciones_message_id (message_id),
  FOREIGN KEY (message_id) REFERENCES mensajes_chat(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
