-- ChargeHero combined schema migration
-- Run this entire file in Supabase SQL Editor (Dashboard -> SQL Editor -> New query)
-- Generated from migrations/001..005 in order


-- ============================================================
-- migrations/001_initial_auth_schema.sql
-- ============================================================
-- Initial authentication schema for ChargeHero
-- This migration creates all tables required for the authentication domain

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Auth users table - core authentication information
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255),
    user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('engineer', 'customer', 'admin')),
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_email CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Engineer registrations table - tracks engineer signup process
CREATE TABLE IF NOT EXISTS auth_engineer_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL UNIQUE REFERENCES auth_users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    business_name VARCHAR(255),
    work_area VARCHAR(100),
    state_abbr VARCHAR(2),
    registration_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (
        registration_status IN ('pending', 'under_review', 'approved', 'rejected', 'suspended')
    ),
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT first_name_not_empty CHECK (first_name IS NULL OR TRIM(first_name) != ''),
    CONSTRAINT last_name_not_empty CHECK (last_name IS NULL OR TRIM(last_name) != '')
);

-- Engineer KYC (Know Your Customer) table - identity verification
CREATE TABLE IF NOT EXISTS auth_engineer_kyc (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL UNIQUE REFERENCES auth_users(id) ON DELETE CASCADE,
    ssn_last_four VARCHAR(4),
    date_of_birth DATE,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_abbr VARCHAR(2),
    zip_code VARCHAR(10),
    country_code VARCHAR(2) DEFAULT 'US',
    kyc_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (
        kyc_status IN ('pending', 'under_review', 'verified', 'failed', 'expired')
    ),
    kyc_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_zip CHECK (zip_code IS NULL OR zip_code ~ '^[0-9]{5}(-[0-9]{4})?$'),
    CONSTRAINT valid_state CHECK (state_abbr IS NULL OR LENGTH(state_abbr) = 2)
);

-- Engineer documents table - stores document metadata and references
CREATE TABLE IF NOT EXISTS auth_engineer_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL CHECK (
        document_type IN ('drivers_license', 'passport', 'national_id', 'business_license', 'insurance', 'certification')
    ),
    document_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size BIGINT,
    document_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (
        document_status IN ('pending', 'approved', 'rejected', 'expired')
    ),
    expiry_date DATE,
    verification_notes TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT document_path_not_empty CHECK (document_path IS NULL OR TRIM(document_path) != '')
);

-- Engineer training table - tracks certifications and training completions
CREATE TABLE IF NOT EXISTS auth_engineer_training (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    training_type VARCHAR(100) NOT NULL,
    training_title VARCHAR(255),
    issuing_organization VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    credential_url VARCHAR(500),
    training_status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (
        training_status IN ('active', 'expired', 'revoked', 'pending_verification')
    ),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Engineer profiles table - extended engineer information
CREATE TABLE IF NOT EXISTS auth_engineer_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL UNIQUE REFERENCES auth_users(id) ON DELETE CASCADE,
    bio TEXT,
    profile_picture_path VARCHAR(500),
    hourly_rate DECIMAL(10, 2),
    service_radius_miles INTEGER,
    preferred_work_areas TEXT,
    years_of_experience INTEGER,
    specializations TEXT,
    availability_status VARCHAR(50) NOT NULL DEFAULT 'available' CHECK (
        availability_status IN ('available', 'unavailable', 'on_break', 'on_job')
    ),
    average_rating DECIMAL(3, 2) DEFAULT 0,
    total_jobs_completed INTEGER DEFAULT 0,
    response_time_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Customer profiles table - customer information and preferences
CREATE TABLE IF NOT EXISTS auth_customer_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID NOT NULL UNIQUE REFERENCES auth_users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_abbr VARCHAR(2),
    zip_code VARCHAR(10),
    country_code VARCHAR(2) DEFAULT 'US',
    preferred_contact_method VARCHAR(50) DEFAULT 'phone' CHECK (
        preferred_contact_method IN ('phone', 'email', 'sms')
    ),
    notification_preferences TEXT,
    profile_picture_path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_zip CHECK (zip_code IS NULL OR zip_code ~ '^[0-9]{5}(-[0-9]{4})?$'),
    CONSTRAINT valid_state CHECK (state_abbr IS NULL OR LENGTH(state_abbr) = 2)
);

-- Create indexes for common queries
CREATE INDEX idx_auth_users_phone_number ON auth_users(phone_number);
CREATE INDEX idx_auth_users_email ON auth_users(email);
CREATE INDEX idx_auth_users_user_type ON auth_users(user_type);
CREATE INDEX idx_auth_users_is_active ON auth_users(is_active);
CREATE INDEX idx_auth_engineer_registrations_user_id ON auth_engineer_registrations(auth_user_id);
CREATE INDEX idx_auth_engineer_registrations_status ON auth_engineer_registrations(registration_status);
CREATE INDEX idx_auth_engineer_kyc_user_id ON auth_engineer_kyc(auth_user_id);
CREATE INDEX idx_auth_engineer_kyc_status ON auth_engineer_kyc(kyc_status);
CREATE INDEX idx_auth_engineer_documents_user_id ON auth_engineer_documents(auth_user_id);
CREATE INDEX idx_auth_engineer_documents_type ON auth_engineer_documents(document_type);
CREATE INDEX idx_auth_engineer_documents_status ON auth_engineer_documents(document_status);
CREATE INDEX idx_auth_engineer_training_user_id ON auth_engineer_training(auth_user_id);
CREATE INDEX idx_auth_engineer_profiles_user_id ON auth_engineer_profiles(auth_user_id);
CREATE INDEX idx_auth_engineer_profiles_availability ON auth_engineer_profiles(availability_status);
CREATE INDEX idx_auth_customer_profiles_user_id ON auth_customer_profiles(auth_user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER auth_users_updated_at BEFORE UPDATE ON auth_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER auth_engineer_registrations_updated_at BEFORE UPDATE ON auth_engineer_registrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER auth_engineer_kyc_updated_at BEFORE UPDATE ON auth_engineer_kyc
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER auth_engineer_documents_updated_at BEFORE UPDATE ON auth_engineer_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER auth_engineer_training_updated_at BEFORE UPDATE ON auth_engineer_training
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER auth_engineer_profiles_updated_at BEFORE UPDATE ON auth_engineer_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER auth_customer_profiles_updated_at BEFORE UPDATE ON auth_customer_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security Policies
-- Enable RLS on all auth tables
ALTER TABLE auth_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_engineer_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_engineer_kyc ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_engineer_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_engineer_training ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_engineer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_customer_profiles ENABLE ROW LEVEL SECURITY;

-- Users can only read their own record
CREATE POLICY users_read_own ON auth_users FOR SELECT
  USING (auth.uid() = id);

-- Admins can read all users
CREATE POLICY admins_read_all ON auth_users FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM auth_users WHERE auth.uid() = id AND user_type = 'admin'
  ));

-- Users can insert their own record (for registration)
CREATE POLICY users_insert_own ON auth_users FOR INSERT
  WITH CHECK (auth.uid() = id OR auth.uid() IS NULL);

-- Users can update their own record
CREATE POLICY users_update_own ON auth_users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Engineer registrations: users can read/write their own
CREATE POLICY engineer_registrations_read_own ON auth_engineer_registrations FOR SELECT
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));

-- Admins can read all registrations
CREATE POLICY engineer_registrations_read_admins ON auth_engineer_registrations FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM auth_users WHERE auth.uid() = id AND user_type = 'admin'
  ));

-- Engineer KYC: users can read/write their own
CREATE POLICY engineer_kyc_read_own ON auth_engineer_kyc FOR SELECT
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));

-- Admins can read all KYC
CREATE POLICY engineer_kyc_read_admins ON auth_engineer_kyc FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM auth_users WHERE auth.uid() = id AND user_type = 'admin'
  ));

-- Engineer documents: users can read/write their own
CREATE POLICY engineer_documents_read_own ON auth_engineer_documents FOR SELECT
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));

-- Admins can read all documents
CREATE POLICY engineer_documents_read_admins ON auth_engineer_documents FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM auth_users WHERE auth.uid() = id AND user_type = 'admin'
  ));

-- Engineer training: users can read/write their own
CREATE POLICY engineer_training_read_own ON auth_engineer_training FOR SELECT
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));

-- Admins can read all training
CREATE POLICY engineer_training_read_admins ON auth_engineer_training FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM auth_users WHERE auth.uid() = id AND user_type = 'admin'
  ));

-- Engineer profiles: users can read/write their own
CREATE POLICY engineer_profiles_read_own ON auth_engineer_profiles FOR SELECT
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));

-- Everyone can read public engineer profiles
CREATE POLICY engineer_profiles_read_public ON auth_engineer_profiles FOR SELECT
  USING (TRUE);

-- Engineer profiles: users can update their own
CREATE POLICY engineer_profiles_update_own ON auth_engineer_profiles FOR UPDATE
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));

-- Customer profiles: users can read/write their own
CREATE POLICY customer_profiles_read_own ON auth_customer_profiles FOR SELECT
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));

-- Admins can read all customer profiles
CREATE POLICY customer_profiles_read_admins ON auth_customer_profiles FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM auth_users WHERE auth.uid() = id AND user_type = 'admin'
  ));

-- Customer profiles: users can update their own
CREATE POLICY customer_profiles_update_own ON auth_customer_profiles FOR UPDATE
  USING (auth.uid() IN (SELECT id FROM auth_users WHERE id = auth_user_id));


-- ============================================================
-- migrations/002_jobs_schema.sql
-- ============================================================
-- migrations/002_jobs_schema.sql
-- Jobs domain tables for ticket management, charger tracking, and dispatch system

-- Chargers table - EV charging stations
CREATE TABLE IF NOT EXISTS jobs_chargers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES auth_users(id),
    serial_number TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    brand TEXT NOT NULL,
    location POINT NOT NULL,
    address TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Tickets table - Service requests for chargers
CREATE TABLE IF NOT EXISTS jobs_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    charger_id UUID NOT NULL REFERENCES jobs_chargers(id),
    customer_id UUID NOT NULL REFERENCES auth_users(id),
    ticket_type TEXT NOT NULL CHECK (ticket_type IN ('preventive_maintenance', 'commission', 'issue')),
    fault_type TEXT,
    description TEXT,
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'assigned', 'in_progress', 'resolved', 'closed')),
    sla_minutes INT DEFAULT 240,
    assigned_engineer_id UUID REFERENCES auth_users(id),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Dispatch assignments table - Track job assignments to engineers
CREATE TABLE IF NOT EXISTS jobs_dispatch_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL UNIQUE REFERENCES jobs_tickets(id),
    engineer_id UUID NOT NULL REFERENCES auth_users(id),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'in_progress', 'completed')),
    assigned_at TIMESTAMP DEFAULT now(),
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    dispatch_score DECIMAL(5, 2),
    last_location POINT,
    created_at TIMESTAMP DEFAULT now()
);

-- Service reports table - Completion details for tickets
CREATE TABLE IF NOT EXISTS jobs_service_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL UNIQUE REFERENCES jobs_tickets(id),
    engineer_id UUID NOT NULL REFERENCES auth_users(id),
    work_description TEXT,
    spare_parts_used TEXT[],
    before_photo_url TEXT,
    after_photo_url TEXT,
    customer_signature_url TEXT,
    resolution_time_minutes INT,
    rating_by_customer INT,
    created_at TIMESTAMP DEFAULT now()
);

-- Engineer skills table - Track certifications and specializations
CREATE TABLE IF NOT EXISTS jobs_engineer_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id),
    charger_type TEXT NOT NULL,
    charger_brand TEXT NOT NULL,
    is_certified BOOLEAN DEFAULT false,
    certified_by UUID REFERENCES auth_users(id),
    certified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(user_id, charger_type, charger_brand)
);

-- Earnings table - Track engineer compensation
CREATE TABLE IF NOT EXISTS jobs_earnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engineer_id UUID NOT NULL REFERENCES auth_users(id),
    ticket_id UUID NOT NULL REFERENCES jobs_tickets(id),
    amount DECIMAL(10, 2),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid')),
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

-- Ticket attachments table - Store file uploads for tickets
CREATE TABLE IF NOT EXISTS jobs_ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES jobs_tickets(id),
    uploaded_by UUID NOT NULL REFERENCES auth_users(id),
    file_url TEXT NOT NULL,
    file_name TEXT,
    file_type TEXT NOT NULL,
    file_size_kb INT,
    description TEXT,
    uploaded_at TIMESTAMP DEFAULT now()
);

-- Indexes for performance optimization
CREATE INDEX idx_jobs_chargers_customer ON jobs_chargers(customer_id);
CREATE INDEX idx_jobs_chargers_location ON jobs_chargers USING GIST(location);
CREATE INDEX idx_jobs_tickets_charger ON jobs_tickets(charger_id);
CREATE INDEX idx_jobs_tickets_status ON jobs_tickets(status);
CREATE INDEX idx_jobs_tickets_assigned_engineer ON jobs_tickets(assigned_engineer_id);
CREATE INDEX idx_jobs_tickets_customer ON jobs_tickets(customer_id);
CREATE INDEX idx_jobs_dispatch_engineer ON jobs_dispatch_assignments(engineer_id);
CREATE INDEX idx_jobs_dispatch_status ON jobs_dispatch_assignments(status);
CREATE INDEX idx_jobs_dispatch_ticket ON jobs_dispatch_assignments(ticket_id);
CREATE INDEX idx_jobs_earnings_engineer ON jobs_earnings(engineer_id);
CREATE INDEX idx_jobs_earnings_ticket ON jobs_earnings(ticket_id);
CREATE INDEX idx_jobs_service_reports_ticket ON jobs_service_reports(ticket_id);
CREATE INDEX idx_jobs_service_reports_engineer ON jobs_service_reports(engineer_id);
CREATE INDEX idx_jobs_engineer_skills_user ON jobs_engineer_skills(user_id);
CREATE INDEX idx_jobs_ticket_attachments_ticket ON jobs_ticket_attachments(ticket_id);


-- ============================================================
-- migrations/003_checklists_schema.sql
-- ============================================================
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


-- ============================================================
-- migrations/004_copilot_schema.sql
-- ============================================================
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


-- ============================================================
-- migrations/005_notifications_schema.sql
-- ============================================================
-- migrations/005_notifications_schema.sql
-- Notifications, user preferences, and activity logging

-- Notifications - Push and in-app notifications
CREATE TABLE IF NOT EXISTS notifications_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id),
    type TEXT NOT NULL CHECK (type IN ('job_assigned', 'job_accepted', 'job_completed', 'payment_received', 'training_assigned', 'kyc_approved', 'kyc_rejected', 'general')),
    title TEXT,
    body TEXT,
    data JSONB,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

-- Notification preferences - User settings for notifications
CREATE TABLE IF NOT EXISTS notifications_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth_users(id),
    push_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    in_app_enabled BOOLEAN DEFAULT true,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    job_assignment BOOLEAN DEFAULT true,
    payment_updates BOOLEAN DEFAULT true,
    training_updates BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Activity log - Audit trail for system actions
CREATE TABLE IF NOT EXISTS shared_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    details JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- SMS log - Track SMS sends for compliance
CREATE TABLE IF NOT EXISTS notifications_sms_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id),
    phone_number TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
    external_id TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

-- Email log - Track email sends for compliance
CREATE TABLE IF NOT EXISTS notifications_email_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id),
    email_address TEXT NOT NULL,
    subject TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
    external_id TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_notifications_user ON notifications_notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications_notifications(is_read);
CREATE INDEX idx_notifications_created ON notifications_notifications(created_at);
CREATE INDEX idx_notifications_type ON notifications_notifications(type);
CREATE INDEX idx_notifications_preferences_user ON notifications_preferences(user_id);
CREATE INDEX idx_activity_log_user ON shared_activity_log(user_id);
CREATE INDEX idx_activity_log_action ON shared_activity_log(action);
CREATE INDEX idx_activity_log_created ON shared_activity_log(created_at);
CREATE INDEX idx_activity_log_resource ON shared_activity_log(resource_type, resource_id);
CREATE INDEX idx_sms_log_user ON notifications_sms_log(user_id);
CREATE INDEX idx_sms_log_status ON notifications_sms_log(status);
CREATE INDEX idx_email_log_user ON notifications_email_log(user_id);
CREATE INDEX idx_email_log_status ON notifications_email_log(status);

