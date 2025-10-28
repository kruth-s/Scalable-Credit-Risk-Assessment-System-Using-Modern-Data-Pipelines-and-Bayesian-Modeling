-- storage/init_db.sql
-- Creates core tables for demo: loan_applications, customer_behavior, features, risk_scores, model_registry

CREATE TABLE IF NOT EXISTS loan_applications (
  application_id UUID PRIMARY KEY,
  customer_id UUID,
  application_date TIMESTAMP,
  loan_amount NUMERIC,
  term INT,
  income NUMERIC,
  employment_status TEXT,
  zip_code TEXT,
  label_default BOOLEAN,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_behavior (
  event_id UUID PRIMARY KEY,
  customer_id UUID,
  event_time TIMESTAMP,
  event_type TEXT,
  amount NUMERIC,
  metadata JSONB
);

CREATE TABLE IF NOT EXISTS features (
  customer_id UUID PRIMARY KEY,
  last_updated TIMESTAMP,
  f_payment_ratio FLOAT,
  f_missed_freq FLOAT,
  f_credit_util FLOAT,
  f_income_loan FLOAT,
  model_version TEXT
);

CREATE TABLE IF NOT EXISTS risk_scores (
  customer_id UUID,
  score FLOAT,
  score_type TEXT,
  model_version TEXT,
  uncertainty FLOAT,
  evaluated_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (customer_id, score_type)
);

CREATE TABLE IF NOT EXISTS model_registry (
  model_version TEXT PRIMARY KEY,
  model_path TEXT,
  created_at TIMESTAMP DEFAULT now(),
  metrics JSONB
);
