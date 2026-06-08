-- migrations/003_checklists_schema.sql
-- Checklist templates and responses for service completion tracking

-- Checklist templates - Reusable checklists for different service types
CREATE TABLE IF NOT EXISTS jobs_checklist_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    checklist_type TEXT NOT NULL CHECK (checklist_type IN ('preventive_maintenance', 'commission', 'issue')),
    charger_brand TEXT,
    charger_model TEXT,
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Checklist items - Individual tasks within a template
CREATE TABLE IF NOT EXISTS jobs_checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES jobs_checklist_templates(id),
    item_number INT,
    task_description TEXT NOT NULL,
    expected_result TEXT,
    is_required BOOLEAN DEFAULT true,
    item_type TEXT DEFAULT 'text' CHECK (item_type IN ('text', 'yes_no', 'photo', 'video', 'signature')),
    created_at TIMESTAMP DEFAULT now()
);

-- Checklist responses - Engineer responses to checklist templates
CREATE TABLE IF NOT EXISTS jobs_checklist_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES jobs_checklist_templates(id),
    ticket_id UUID NOT NULL REFERENCES jobs_tickets(id),
    engineer_id UUID NOT NULL REFERENCES auth_users(id),
    status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed_by_engineer', 'submitted_to_customer', 'approved_by_customer', 'rejected_by_customer')),
    started_at TIMESTAMP,
    completed_by_engineer_at TIMESTAMP,
    submitted_to_customer_at TIMESTAMP,
    approved_by_customer_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Checklist item responses - Engineer's response to individual items
CREATE TABLE IF NOT EXISTS jobs_checklist_item_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checklist_response_id UUID NOT NULL REFERENCES jobs_checklist_responses(id),
    checklist_item_id UUID NOT NULL REFERENCES jobs_checklist_items(id),
    response_value TEXT,
    passed BOOLEAN,
    notes TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Checklist item media - Photos/videos/signatures for checklist items
CREATE TABLE IF NOT EXISTS jobs_checklist_item_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checklist_item_response_id UUID NOT NULL REFERENCES jobs_checklist_item_responses(id),
    media_url TEXT NOT NULL,
    media_type TEXT NOT NULL CHECK (media_type IN ('photo', 'video', 'signature')),
    uploaded_by UUID NOT NULL REFERENCES auth_users(id),
    uploaded_at TIMESTAMP DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_jobs_checklist_templates_type ON jobs_checklist_templates(checklist_type);
CREATE INDEX idx_jobs_checklist_templates_brand ON jobs_checklist_templates(charger_brand);
CREATE INDEX idx_jobs_checklist_responses_ticket ON jobs_checklist_responses(ticket_id);
CREATE INDEX idx_jobs_checklist_responses_engineer ON jobs_checklist_responses(engineer_id);
CREATE INDEX idx_jobs_checklist_responses_status ON jobs_checklist_responses(status);
CREATE INDEX idx_jobs_checklist_responses_template ON jobs_checklist_responses(template_id);
CREATE INDEX idx_jobs_checklist_item_responses_response ON jobs_checklist_item_responses(checklist_response_id);
CREATE INDEX idx_jobs_checklist_item_responses_item ON jobs_checklist_item_responses(checklist_item_id);
CREATE INDEX idx_jobs_checklist_item_media_response ON jobs_checklist_item_media(checklist_item_response_id);
