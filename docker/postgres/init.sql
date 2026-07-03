-- =====================================================
-- PostgreSQL Initialization Script
-- Chatbot Engine - Database Schema
-- =====================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. Internal Products
-- =====================================================

CREATE TABLE internal_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    product_id VARCHAR(100) UNIQUE NOT NULL,

    product_name VARCHAR(150) NOT NULL,

    internal_service_token_hash TEXT NOT NULL,

    ui_theme_config JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. Bots
-- =====================================================

CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    product_id UUID NOT NULL,

    bot_name VARCHAR(100) NOT NULL,

    description TEXT,

    status VARCHAR(20) DEFAULT 'ACTIVE',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id)
        REFERENCES internal_products(id)
        ON DELETE CASCADE
);

-- =====================================================
-- 3. Document Registry
-- =====================================================

CREATE TABLE document_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    bot_id UUID NOT NULL,

    filename TEXT NOT NULL,

    storage_path TEXT NOT NULL,

    document_hash TEXT UNIQUE NOT NULL,

    processing_status VARCHAR(30) DEFAULT 'PENDING',

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bot_id)
        REFERENCES bots(id)
        ON DELETE CASCADE
);

-- =====================================================
-- 4. Bot Settings
-- =====================================================

CREATE TABLE bot_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    bot_id UUID UNIQUE NOT NULL,

    llm_model VARCHAR(100),

    embedding_model VARCHAR(100),

    system_prompt TEXT,

    temperature DECIMAL(3,2),

    top_k INTEGER DEFAULT 5,

    language VARCHAR(20),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bot_id)
        REFERENCES bots(id)
        ON DELETE CASCADE
);

-- =====================================================
-- 5. Chat Sessions
-- =====================================================

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    bot_id UUID NOT NULL,

    session_identifier TEXT,

    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    ended_at TIMESTAMP,

    FOREIGN KEY (bot_id)
        REFERENCES bots(id)
        ON DELETE CASCADE
);

-- =====================================================
-- 6. Messages
-- =====================================================

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    session_id UUID NOT NULL,

    sender VARCHAR(20) NOT NULL,

    message TEXT NOT NULL,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE
);

-- =====================================================
-- 7. Analytics (Optional)
-- =====================================================

CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    bot_id UUID NOT NULL,

    total_conversations INTEGER DEFAULT 0,

    average_response_time FLOAT,

    total_tokens INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bot_id)
        REFERENCES bots(id)
        ON DELETE CASCADE
);