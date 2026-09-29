CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
  id          BIGSERIAL PRIMARY KEY,
  tenant_id   TEXT NOT NULL,
  source      TEXT NOT NULL,
  doc_type    TEXT,
  content     TEXT NOT NULL,
  content_sha TEXT NOT NULL,
  embedding   VECTOR(1024) NOT NULL,
  tsv         TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  created_at  TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, content_sha)
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks USING gin (tsv);
CREATE INDEX ON chunks (tenant_id);

ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON chunks
  USING (tenant_id = current_setting('app.tenant_id'));
