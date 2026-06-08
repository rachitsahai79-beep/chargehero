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
