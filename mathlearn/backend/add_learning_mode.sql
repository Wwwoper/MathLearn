-- Добавление колонки learning_mode в таблицу users, если она отсутствует
ALTER TABLE users ADD COLUMN IF NOT EXISTS learning_mode VARCHAR(20) DEFAULT 'classic' NOT NULL;
