-- migrations/004_copilot_schema.sql
-- AI Copilot knowledge base, diagnostics, and predictions tables

-- Knowledge base - Technical information for AI diagnosis
CREATE TABLE IF NOT EXISTS copilot_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fault_type TEXT NOT NULL,
    root_cause TEXT,
    test_procedure TEXT,
    spare_parts_needed TEXT[],
    safety_sop TEXT,
    charger_brand TEXT,
    charger_model TEXT,
    created_by UUID REFERENCES auth_users(id),
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Diagnostics - AI diagnosis records for troubleshooting
CREATE TABLE IF NOT EXISTS copilot_diagnostics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES jobs_tickets(id),
    engineer_id UUID NOT NULL REFERENCES auth_users(id),
    fault_description TEXT NOT NULL,
    ai_diagnosis TEXT,
    ai_confidence DECIMAL(3, 2),
    was_helpful BOOLEAN,
    actual_resolution TEXT,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Predictions - Predictive maintenance based on charger patterns
CREATE TABLE IF NOT EXISTS copilot_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    charger_id UUID NOT NULL REFERENCES jobs_chargers(id),
    failure_type TEXT NOT NULL,
    probability DECIMAL(3, 2),
    days_until_failure INT,
    recommended_action TEXT,
    confidence_level TEXT DEFAULT 'medium' CHECK (confidence_level IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT now()
);

-- Conversation history - Store AI chatbot interactions
CREATE TABLE IF NOT EXISTS copilot_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id),
    ticket_id UUID REFERENCES jobs_tickets(id),
    context JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- Conversation messages - Individual messages in a conversation
CREATE TABLE IF NOT EXISTS copilot_conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES copilot_conversations(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    token_count INT,
    created_at TIMESTAMP DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_copilot_knowledge_base_fault ON copilot_knowledge_base(fault_type);
CREATE INDEX idx_copilot_knowledge_base_brand ON copilot_knowledge_base(charger_brand);
CREATE INDEX idx_copilot_diagnostics_ticket ON copilot_diagnostics(ticket_id);
CREATE INDEX idx_copilot_diagnostics_engineer ON copilot_diagnostics(engineer_id);
CREATE INDEX idx_copilot_diagnostics_created ON copilot_diagnostics(created_at);
CREATE INDEX idx_copilot_predictions_charger ON copilot_predictions(charger_id);
CREATE INDEX idx_copilot_predictions_failure ON copilot_predictions(failure_type);
CREATE INDEX idx_copilot_conversations_user ON copilot_conversations(user_id);
CREATE INDEX idx_copilot_conversations_ticket ON copilot_conversations(ticket_id);
CREATE INDEX idx_copilot_messages_conversation ON copilot_conversation_messages(conversation_id);
