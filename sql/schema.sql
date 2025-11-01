CREATE TABLE IF NOT EXISTS raw_content (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id VARCHAR(100) NOT NULL,
  published_at TIMESTAMP NOT NULL,
  title TEXT NOT NULL,
  raw_text TEXT,
  url TEXT,
  collected_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR(20) DEFAULT 'new',
  metadata JSONB
);

CREATE TABLE IF NOT EXISTS candidate_strategy (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_content_id UUID REFERENCES raw_content(id) ON DELETE CASCADE,
  is_strategy BOOLEAN NOT NULL,
  style VARCHAR(20),
  core_claim TEXT,
  entry_rule TEXT,
  exit_rule TEXT,
  risk_control TEXT,
  score_heat FLOAT,
  score_recency FLOAT,
  score_final FLOAT,
  status VARCHAR(20) DEFAULT 'pending',
  analyzed_at TIMESTAMP DEFAULT NOW(),
  analysis_metadata JSONB
);

CREATE TABLE IF NOT EXISTS pk_result (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_strategy_id UUID REFERENCES candidate_strategy(id) ON DELETE CASCADE,
  symbol_tested VARCHAR(10) NOT NULL,
  period VARCHAR(10) NOT NULL,
  total_return_pct FLOAT,
  max_drawdown_pct FLOAT,
  win_rate_pct FLOAT,
  sharpe_ratio FLOAT,
  style VARCHAR(20),
  summary_for_host TEXT,
  rank_in_style INTEGER,
  status VARCHAR(20),
  backtested_at TIMESTAMP DEFAULT NOW(),
  backtest_metadata JSONB
);

CREATE TABLE IF NOT EXISTS episodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_date DATE NOT NULL UNIQUE,
  short_term_strategy_id UUID REFERENCES pk_result(id),
  long_term_strategy_id UUID REFERENCES pk_result(id),
  script_path TEXT,
  markdown_path TEXT,
  audio_path TEXT,
  published_at TIMESTAMP,
  status VARCHAR(20) DEFAULT 'draft',
  metadata JSONB
);
