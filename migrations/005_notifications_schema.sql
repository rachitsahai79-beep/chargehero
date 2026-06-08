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
