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
