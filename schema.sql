-- ================================================================
-- POSTGRESQL SCHEMA FOR ASTRA MEMORY SYSTEM
-- ================================================================

-- 1. USERS TABLE (Enhanced from existing SQLite)
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    birth_date DATE NOT NULL,
    birth_time TIME NOT NULL,
    birth_location VARCHAR(500) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    timezone VARCHAR(100) NOT NULL,
    natal_chart JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);


-- 2. USER PROFILES (Long-term characteristics)
CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,

    -- Preferences
    preferred_language VARCHAR(50) DEFAULT 'hinglish',
    communication_style VARCHAR(50),
    topics_of_interest TEXT[],

    -- LLM-detected traits
    personality_traits JSONB,
    emotional_patterns JSONB,
    consultation_history_summary TEXT,

    -- Metadata
    last_interaction TIMESTAMP,
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_last_interaction ON user_profiles(last_interaction);


-- 3. USER FACTS (Extracted knowledge)
CREATE TABLE IF NOT EXISTS user_facts (
    fact_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,

    -- Fact details
    fact_type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    fact_text TEXT NOT NULL,
    fact_summary VARCHAR(500),

    -- Temporal info
    fact_timeframe VARCHAR(100),
    mentioned_date DATE,

    -- Metadata
    source_conversation_id INTEGER,
    confidence_score DECIMAL(3, 2),
    importance_score DECIMAL(3, 2),
    status VARCHAR(50) DEFAULT 'active',

    -- Timestamps
    extracted_at TIMESTAMP DEFAULT NOW(),
    last_referenced TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_facts_user_id ON user_facts(user_id);
CREATE INDEX IF NOT EXISTS idx_facts_category ON user_facts(category);
CREATE INDEX IF NOT EXISTS idx_facts_importance ON user_facts(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_facts_status ON user_facts(status);


-- 4. CONVERSATIONS (Enhanced message log)
CREATE TABLE IF NOT EXISTS conversations (
    conv_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,

    -- Message content
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,

    -- Metadata
    message_index INTEGER,
    language_detected VARCHAR(50),
    intent_detected VARCHAR(100),
    topics TEXT[],

    -- Timestamps
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp DESC);


-- 5. CONVERSATION SUMMARIES (Session-level memory)
CREATE TABLE IF NOT EXISTS conversation_summaries (
    summary_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,

    -- Summary content
    summary_text TEXT NOT NULL,
    key_topics TEXT[],
    emotional_state VARCHAR(100),

    -- Advice tracking
    remedies_suggested JSONB,
    follow_up_items TEXT[],
    astrological_insights TEXT[],

    -- Session metadata
    message_count INTEGER,
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    session_duration_minutes INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_summaries_user_id ON conversation_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_summaries_session_start ON conversation_summaries(session_start DESC);


-- 6. CACHE PERFORMANCE (Track OpenAI caching effectiveness)
CREATE TABLE IF NOT EXISTS cache_performance (
    stat_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    session_id VARCHAR(100),
    total_input_tokens INTEGER,
    cached_tokens INTEGER,
    cache_hit_rate DECIMAL(5, 2),
    cost_saved DECIMAL(10, 6),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cache_user_id ON cache_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_cache_timestamp ON cache_performance(timestamp DESC);


-- 7. MEMORY CONSOLIDATION LOG (Track LLM memory extraction)
CREATE TABLE IF NOT EXISTS memory_consolidation_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(100),

    -- Consolidation details
    consolidation_type VARCHAR(50),
    input_message_count INTEGER,
    facts_extracted INTEGER DEFAULT 0,
    summary_generated BOOLEAN DEFAULT FALSE,

    -- LLM usage tracking
    llm_model_used VARCHAR(100),
    tokens_used INTEGER,
    processing_time_ms INTEGER,

    -- Status
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,

    -- Timestamp
    consolidated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consolidation_user_id ON memory_consolidation_log(user_id);
CREATE INDEX IF NOT EXISTS idx_consolidation_date ON memory_consolidation_log(consolidated_at DESC);
