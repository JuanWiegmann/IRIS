-- KIM Database Initialization
-- PostgreSQL + pgvector for 3NF + vector similarity
--
-- Research basis:
-- - Wu et al. (2024): User outputs drive personalization
-- - Westhaeusser et al. (2025): Multi-tiered memory (STM/LTM)
-- - GATE (Li et al., ICLR 2025): Target-based onboarding

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ═══════════════════════════════════════════════════════════
-- CORE PROFILE TABLE (3NF)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE user_profile (
    id UUID PRIMARY KEY,
    language VARCHAR(10) NOT NULL DEFAULT 'en-US',
    format_preference VARCHAR(50) NOT NULL DEFAULT 'concise',
    confidence DECIMAL(3,2) NOT NULL DEFAULT 0.00 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    recent_context TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for lookups
CREATE INDEX idx_user_profile_updated ON user_profile(updated_at DESC);

COMMENT ON TABLE user_profile IS 'Core user profile (atomic attributes only - 3NF compliant)';
COMMENT ON COLUMN user_profile.confidence IS 'Overall profile confidence (0.0=new, 1.0=well-established)';

-- ═══════════════════════════════════════════════════════════
-- USER TONE (Normalized - one-to-many)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE user_tone (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    tone VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, tone)
);

CREATE INDEX idx_user_tone_user ON user_tone(user_id);

COMMENT ON TABLE user_tone IS 'User tone preferences (normalized from profile array)';
COMMENT ON COLUMN user_tone.priority IS 'Order of importance (1=highest)';

-- ═══════════════════════════════════════════════════════════
-- USER BOUNDARIES (Normalized - one-to-many)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE user_boundary (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    rule TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_boundary_user ON user_boundary(user_id);

COMMENT ON TABLE user_boundary IS 'User boundaries/constraints (normalized from profile dict)';

-- ═══════════════════════════════════════════════════════════
-- USER PROJECTS (Normalized - one-to-many)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE user_project (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    project_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, project_name)
);

CREATE INDEX idx_user_project_user_active ON user_project(user_id, is_active);

COMMENT ON TABLE user_project IS 'User current projects (normalized from profile array)';

-- ═══════════════════════════════════════════════════════════
-- USER OUTPUTS (Segment 3 - ready for implementation)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE user_output (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    context VARCHAR(500),
    output_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB,
    -- Full-text search
    content_tsvector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    -- Vector embedding (Segment 3)
    embedding vector(768)
);

CREATE INDEX idx_user_output_user_created ON user_output(user_id, created_at DESC);
CREATE INDEX idx_user_output_tsvector ON user_output USING GIN(content_tsvector);
CREATE INDEX idx_user_output_embedding ON user_output USING hnsw (embedding vector_cosine_ops);

COMMENT ON TABLE user_output IS 'User past outputs (emails, documents, code) - Wu et al. 2024';
COMMENT ON COLUMN user_output.content_tsvector IS 'Full-text search vector (BM25)';
COMMENT ON COLUMN user_output.embedding IS 'Semantic embedding for similarity search (768D)';

-- ═══════════════════════════════════════════════════════════
-- MEMORY ENTRIES (Multi-tiered memory - Westhaeusser et al.)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE memory_entry (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('STM', 'summary', 'LTM')),
    content TEXT NOT NULL,
    importance DECIMAL(3,2) CHECK (importance >= 0.0 AND importance <= 1.0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    embedding vector(768)
);

CREATE INDEX idx_memory_user_type ON memory_entry(user_id, type);
CREATE INDEX idx_memory_expires ON memory_entry(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE memory_entry IS 'Multi-tiered memory (STM=24h, LTM=permanent) - Westhaeusser 2025';
COMMENT ON COLUMN memory_entry.expires_at IS 'STM entries expire after 24h';

-- ═══════════════════════════════════════════════════════════
-- ONBOARDING TARGETS (GATE methodology - Segment 5)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE onboarding_target (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    dimension VARCHAR(100) NOT NULL,
    research_basis TEXT NOT NULL,
    barrier_type VARCHAR(50) NOT NULL,
    barrier_threshold JSONB,
    satisfied BOOLEAN DEFAULT FALSE,
    confidence DECIMAL(3,2) DEFAULT 0.00 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    evidence JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    satisfied_at TIMESTAMP
);

CREATE INDEX idx_onboarding_user_satisfied ON onboarding_target(user_id, satisfied);

COMMENT ON TABLE onboarding_target IS 'GATE onboarding targets with barriers - Li et al. ICLR 2025';
COMMENT ON COLUMN onboarding_target.evidence IS 'Array of evidence entries for barrier satisfaction';

-- ═══════════════════════════════════════════════════════════
-- TRIGGER: Auto-update updated_at
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_profile_updated_at
    BEFORE UPDATE ON user_profile
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ═══════════════════════════════════════════════════════════
-- INITIAL DATA (Demo user for testing)
-- ═══════════════════════════════════════════════════════════

-- Create demo user profile
INSERT INTO user_profile (id, language, format_preference, confidence)
VALUES ('00000000-0000-0000-0000-000000000001', 'en-US', 'concise', 0.10);

INSERT INTO user_tone (user_id, tone, priority)
VALUES ('00000000-0000-0000-0000-000000000001', 'professional', 1);

-- ═══════════════════════════════════════════════════════════
-- VIEWS FOR CONVENIENCE
-- ═══════════════════════════════════════════════════════════

-- Complete profile view (joins normalized tables)
CREATE VIEW v_user_profile_complete AS
SELECT
    p.*,
    array_agg(t.tone ORDER BY t.priority) FILTER (WHERE t.tone IS NOT NULL) AS tones,
    jsonb_object_agg(b.category, b.rule) FILTER (WHERE b.category IS NOT NULL) AS boundaries,
    array_agg(pr.project_name ORDER BY pr.started_at) FILTER (WHERE pr.is_active AND pr.project_name IS NOT NULL) AS current_projects
FROM user_profile p
LEFT JOIN user_tone t ON p.id = t.user_id
LEFT JOIN user_boundary b ON p.id = b.user_id
LEFT JOIN user_project pr ON p.id = pr.user_id
GROUP BY p.id;

COMMENT ON VIEW v_user_profile_complete IS 'Denormalized view of complete profile (for easy reading)';
