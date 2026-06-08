# ChargeHero: Full-Stack Slice Design Document

**Version:** 1.0  
**Date:** 2026-06-08  
**Project:** ChargeHero - EV Charging Service Management Platform  
**Scope:** Engineer App MVP + Backend Foundation + Customer/Admin Portal Framework

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Vision & Scope](#vision--scope)
3. [System Architecture](#system-architecture)
4. [Database Schema](#database-schema)
5. [Engineer App: Screens & Flows](#engineer-app-screens--flows)
6. [Backend APIs](#backend-apis)
7. [Real-time Features & Deployment](#real-time-features--deployment)
8. [Tech Stack](#tech-stack)
9. [Customer App & Admin Portal (Overview)](#customer-app--admin-portal-overview)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Success Criteria](#success-criteria)

---

## Executive Summary

ChargeHero is an enterprise EV charging service management platform. This document specifies the **full-stack MVP slice**:

- **Engineer App (Flutter Android):** Self-service registration → KYC verification → Training assignment → Job dispatch → Service completion with digital checklists
- **Backend (FastAPI + Supabase):** Auth, job dispatch, AI copilot, notifications, real-time tracking
- **Customer App & Admin Portal:** Parallel deliverables, same tech stack

**Timeline:** 6-8 weeks (continuous AI-assisted development)  
**Deployment:** Supabase (free tier) + Render/Railway (free tier) + Firebase + S3-compatible storage  
**Key Principle:** Monolithic backend with clear domain boundaries, extraction-ready for microservices at scale

---

## Vision & Scope

### What We're Building

1. **Engineer Self-Registration Pipeline**
   - Engineers register via phone
   - Submit video KYC with Aadhaar
   - Upload 10th, 12th, ITI certificates
   - Admin verifies KYC + documents
   - Training dates assigned
   - Post-training, engineers access job platform

2. **Job Dispatch & Service Completion**
   - Real-time job assignments based on skill match + location + rating
   - Live navigation to job site
   - Dynamic checklist (Preventive Maintenance, Commission, or Issue-specific)
   - Photo/video evidence capture
   - Customer signature collection
   - Service report submitted to customer for approval

3. **AI Copilot (Phase 1)**
   - Engineers ask: "Isolation fault in ABB 22kW charger"
   - System returns: root cause, test procedure, spare parts, safety SOP
   - Powered by Claude API + knowledge base

4. **Real-time Features**
   - Engineers receive job assignments in real-time
   - Customers track engineer location live
   - Notifications for all key events
   - Push + in-app messaging

### What's NOT in MVP

- Training Academy (Phase 2)
- Spare parts marketplace (Phase 2)
- Advanced predictive maintenance (Phase 2)
- Multi-language support (Phase 2)
- OEM integrations (Phase 2)

---

## System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter Apps                          │
│  Engineer App | Customer App | Admin Portal              │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    ┌───▼────────┐      ┌──────▼────────┐
    │ REST APIs  │      │ WebSocket     │
    │ (FastAPI)  │      │ Real-time     │
    └───┬────────┘      └──────┬────────┘
        │                       │
    ┌───▼──────────────────────▼──────────┐
    │   FastAPI Monolith (Single Process) │
    │                                      │
    │  ┌──────────┐  ┌──────────┐ ┌─────┐│
    │  │ Auth     │  │ Jobs &   │ │AI   ││
    │  │Domain    │  │Dispatch  │ │Copi ││
    │  └──────────┘  └──────────┘ │lot  ││
    │                             └─────┘│
    │  ┌──────────┐  ┌──────────┐       │
    │  │Notif.    │  │Shared    │       │
    │  │Domain    │  │Utils     │       │
    │  └──────────┘  └──────────┘       │
    └───┬──────────────────────────────────┘
        │
    ┌───▼──────────────────────┐
    │   Supabase               │
    │  (PostgreSQL + Auth)     │
    │                          │
    │  Tables organized by     │
    │  domain (auth_*, jobs_*) │
    └────────────────────────┘
```

### Domain Ownership

| Domain | Responsibility | Key Tables |
|--------|---|---|
| **Auth** | User registration, KYC, JWT, RBAC | `auth_users`, `auth_engineer_registrations`, `auth_engineer_kyc`, `auth_engineer_documents`, `auth_engineer_training` |
| **Jobs & Dispatch** | Tickets, job assignment, dispatch algorithm | `jobs_chargers`, `jobs_tickets`, `jobs_dispatch_assignments`, `jobs_service_reports`, `jobs_checklist_*` |
| **Copilot** | AI diagnosis, knowledge base | `copilot_knowledge_base`, `copilot_diagnostics`, `copilot_predictions` |
| **Notifications** | Push, SMS, in-app messaging | `notifications_notifications`, `notifications_preferences` |
| **Shared** | Utilities, logging, error handling | `shared_activity_log` |

---

## Database Schema

### Auth Domain

```sql
-- Core user table (extended from Supabase Auth)
auth_users (
  id: UUID PK,
  role: TEXT ('engineer', 'customer', 'admin'),
  status: TEXT ('active', 'inactive', 'suspended'),
  name, email, phone: TEXT,
  created_at, updated_at: TIMESTAMP
)

-- Engineer extended profile
auth_engineer_profiles (
  id: UUID PK,
  user_id: UUID FK → auth_users,
  certification_level: TEXT ('beginner', 'intermediate', 'expert'),
  rating: DECIMAL(3,2) = 5.0,
  availability: BOOLEAN = true,
  gps_location: POINT (PostGIS),
  bank_account, ifsc_code, upi_id: TEXT,
  created_at: TIMESTAMP
)

-- Registration tracking
auth_engineer_registrations (
  id: UUID PK,
  phone, email: TEXT UNIQUE,
  name: TEXT, dob: DATE,
  bank_account, ifsc_code, upi_id: TEXT,
  status: TEXT ('phone_verified', 'basic_info_submitted', 'kyc_pending', 
                 'kyc_approved', 'kyc_rejected', 'training_assigned', 'training_completed'),
  created_at, updated_at: TIMESTAMP
)

-- Video KYC
auth_engineer_kyc (
  id: UUID PK,
  registration_id: UUID FK → auth_engineer_registrations,
  aadhaar_number: TEXT (masked),
  kyc_video_url, kyc_photo_url: TEXT,
  liveness_verified: BOOLEAN,
  verified_by: UUID FK → auth_users (admin),
  verified_at: TIMESTAMP,
  rejection_reason: TEXT,
  created_at: TIMESTAMP
)

-- Document uploads
auth_engineer_documents (
  id: UUID PK,
  registration_id: UUID FK → auth_engineer_registrations,
  document_type: TEXT ('10th_certificate', '12th_certificate', 'iti_certificate'),
  document_url: TEXT (S3),
  file_name: TEXT,
  uploaded_at: TIMESTAMP
)

-- Training assignment
auth_engineer_training (
  id: UUID PK,
  registration_id: UUID FK → auth_engineer_registrations,
  training_start_date, training_end_date: DATE,
  training_location: TEXT,
  assigned_by: UUID FK → auth_users,
  assigned_at: TIMESTAMP,
  status: TEXT ('assigned', 'in_progress', 'completed', 'failed'),
  completed_at: TIMESTAMP,
  certification_number: TEXT,
  created_at: TIMESTAMP
)

-- Customer extended profile
auth_customer_profiles (
  id: UUID PK,
  user_id: UUID FK → auth_users,
  company_name, address, city, state, pincode: TEXT,
  created_at: TIMESTAMP
)
```

### Jobs & Dispatch Domain

```sql
-- Chargers (assets)
jobs_chargers (
  id: UUID PK,
  customer_id: UUID FK → auth_users,
  serial_number: TEXT UNIQUE,
  model: TEXT ('3.3kW', '7.4kW', '22kW', '30kW', '60kW', '120kW', '240kW'),
  brand: TEXT ('ABB', 'Delta', 'Exicom', 'Servotech', ...),
  location: POINT (GPS),
  address: TEXT,
  status: TEXT ('active', 'inactive', 'maintenance'),
  created_at, updated_at: TIMESTAMP
)

-- Tickets (service requests)
jobs_tickets (
  id: UUID PK,
  charger_id: UUID FK → jobs_chargers,
  customer_id: UUID FK → auth_users,
  ticket_type: TEXT ('preventive_maintenance', 'commission', 'issue'),
  fault_type: TEXT (only for 'issue'),
  description: TEXT,
  priority: TEXT ('low', 'medium', 'high', 'critical'),
  status: TEXT ('open', 'assigned', 'in_progress', 'resolved', 'closed'),
  sla_minutes: INT = 240,
  assigned_engineer_id: UUID FK → auth_users,
  created_at, updated_at: TIMESTAMP
)

-- Dispatch assignments
jobs_dispatch_assignments (
  id: UUID PK,
  ticket_id: UUID FK → jobs_tickets UNIQUE,
  engineer_id: UUID FK → auth_users,
  status: TEXT ('pending', 'accepted', 'rejected', 'in_progress', 'completed'),
  assigned_at, accepted_at, completed_at: TIMESTAMP,
  dispatch_score: DECIMAL(5,2),
  last_location: POINT,
  created_at: TIMESTAMP
)

-- Service reports
jobs_service_reports (
  id: UUID PK,
  ticket_id: UUID FK → jobs_tickets UNIQUE,
  engineer_id: UUID FK → auth_users,
  work_description: TEXT,
  spare_parts_used: TEXT[],
  before_photo_url, after_photo_url, customer_signature_url: TEXT,
  resolution_time_minutes: INT,
  rating_by_customer: INT (1-5),
  created_at: TIMESTAMP
)

-- Engineer skill matrix
jobs_engineer_skills (
  id: UUID PK,
  user_id: UUID FK → auth_users,
  charger_type: TEXT ('3.3kW', '7.4kW', ...),
  charger_brand: TEXT ('ABB', 'Delta', ...),
  is_certified: BOOLEAN,
  certified_by: UUID FK → auth_users,
  certified_at: TIMESTAMP,
  UNIQUE(user_id, charger_type, charger_brand)
)

-- Earnings tracking
jobs_earnings (
  id: UUID PK,
  engineer_id: UUID FK → auth_users,
  ticket_id: UUID FK → jobs_tickets,
  amount: DECIMAL(10,2),
  status: TEXT ('pending', 'paid'),
  paid_at: TIMESTAMP,
  created_at: TIMESTAMP
)

-- Checklist templates
jobs_checklist_templates (
  id: UUID PK,
  name: TEXT ('Preventive Maintenance', 'Commission', 'General Issue'),
  checklist_type: TEXT ('preventive_maintenance', 'commission', 'issue'),
  charger_brand: TEXT (NULL = all brands),
  charger_model: TEXT (NULL = all models),
  is_active: BOOLEAN = true,
  created_at, updated_at: TIMESTAMP
)

-- Checklist items (tasks within template)
jobs_checklist_items (
  id: UUID PK,
  template_id: UUID FK → jobs_checklist_templates,
  item_number: INT,
  task_description: TEXT,
  expected_result: TEXT,
  is_required: BOOLEAN = true,
  created_at: TIMESTAMP
)

-- Checklist responses (engineer's completion)
jobs_checklist_responses (
  id: UUID PK,
  template_id: UUID FK → jobs_checklist_templates,
  ticket_id: UUID FK → jobs_tickets,
  engineer_id: UUID FK → auth_users,
  status: TEXT ('in_progress', 'completed_by_engineer', 'submitted_to_customer',
                 'approved_by_customer', 'rejected_by_customer'),
  started_at, completed_by_engineer_at, submitted_to_customer_at, approved_by_customer_at: TIMESTAMP,
  rejection_reason: TEXT,
  created_at: TIMESTAMP
)

-- Checklist item responses (engineer's answers + media)
jobs_checklist_item_responses (
  id: UUID PK,
  checklist_response_id: UUID FK → jobs_checklist_responses,
  checklist_item_id: UUID FK → jobs_checklist_items,
  response_value: TEXT,
  passed: BOOLEAN,
  notes: TEXT,
  created_at: TIMESTAMP
)

-- Checklist item media (photos/videos)
jobs_checklist_item_media (
  id: UUID PK,
  checklist_item_response_id: UUID FK → jobs_checklist_item_responses,
  media_url: TEXT (S3),
  media_type: TEXT ('image/jpeg', 'video/mp4', ...),
  uploaded_by: UUID FK → auth_users,
  uploaded_at: TIMESTAMP
)

-- Generic ticket attachments
jobs_ticket_attachments (
  id: UUID PK,
  ticket_id: UUID FK → jobs_tickets,
  uploaded_by: UUID FK → auth_users,
  file_url: TEXT (S3),
  file_name, file_type: TEXT,
  file_size_kb: INT,
  description: TEXT,
  uploaded_at: TIMESTAMP
)
```

### Copilot Domain

```sql
-- Knowledge base (AI training data)
copilot_knowledge_base (
  id: UUID PK,
  fault_type: TEXT ('isolation_fault', 'gun_failure', ...),
  root_cause: TEXT,
  test_procedure: TEXT,
  spare_parts_needed: TEXT[],
  safety_sop: TEXT,
  embedding: VECTOR(1536) (OpenAI/Claude embeddings),
  created_at, updated_at: TIMESTAMP
)

-- Diagnostic requests & responses
copilot_diagnostics (
  id: UUID PK,
  ticket_id: UUID FK → jobs_tickets,
  engineer_id: UUID FK → auth_users,
  fault_description: TEXT,
  ai_diagnosis: TEXT,
  ai_confidence: DECIMAL(3,2),
  was_helpful: BOOLEAN,
  actual_resolution: TEXT,
  created_at: TIMESTAMP
)

-- Predictive maintenance
copilot_predictions (
  id: UUID PK,
  charger_id: UUID FK → jobs_chargers,
  failure_type: TEXT,
  probability: DECIMAL(3,2),
  days_until_failure: INT,
  recommended_action: TEXT,
  created_at: TIMESTAMP
)
```

### Notifications Domain

```sql
-- Notification log
notifications_notifications (
  id: UUID PK,
  user_id: UUID FK → auth_users,
  type: TEXT ('job_assigned', 'job_completed', 'kyc_approved', ...),
  title, body: TEXT,
  data: JSONB,
  is_read: BOOLEAN = false,
  read_at: TIMESTAMP,
  created_at: TIMESTAMP
)

-- User notification preferences
notifications_preferences (
  id: UUID PK,
  user_id: UUID FK → auth_users UNIQUE,
  push_enabled, sms_enabled, email_enabled: BOOLEAN = true,
  quiet_hours_start, quiet_hours_end: TIME,
  created_at: TIMESTAMP
)
```

### Shared

```sql
-- Activity audit trail
shared_activity_log (
  id: UUID PK,
  user_id: UUID FK → auth_users,
  action: TEXT ('ticket_created', 'job_accepted', ...),
  resource_type: TEXT ('ticket', 'charger', ...),
  resource_id: UUID,
  details: JSONB,
  created_at: TIMESTAMP
)
```

---

## Engineer App: Screens & Flows

### Screen List (11 Screens)

| # | Screen | Purpose | Key Components |
|---|--------|---------|-----------------|
| 1 | **Splash** | Startup | Logo, version, auto-login |
| 2 | **Login/Register** | Auth entry | "Login" & "Register as Engineer" buttons |
| 3 | **Registration - Step 1** | Phone verification | Phone input, OTP, Next |
| 4 | **Registration - Step 2** | Basic info | Name, DOB, bank details, Next |
| 5 | **Registration - Step 3** | Video KYC | Camera, Aadhaar, liveness, Next |
| 6 | **Registration - Step 4** | Document upload | 10th, 12th, ITI certs, Submit |
| 7 | **Registration Pending** | Confirmation | "Under review" message |
| 8 | **Training Schedule** | Training assignment | Dates, location, [Mark Complete] |
| 9 | **Dashboard** | Home | Jobs summary, earnings, quick actions |
| 10 | **Job Dashboard** | Job list | 4 tabs: Available, Assigned, In Progress, Completed |
| 11 | **Job Details** | Job deep-dive | Customer, charger, fault, SLA, [Accept/Reject] |
| 12 | **Live Navigation** | Route to site | Maps, ETA, [Call], [Start Service] |
| 13 | **Checklist** | Task completion | Dynamic items, photos/video, pass/fail |
| 14 | **Service Report** | Completion proof | Work desc, photos, signature, [Submit] |
| 15 | **Earnings Dashboard** | Payment tracking | Daily/Weekly/Monthly, graph, [Request Payout] |

### Registration Flow (New Engineers)

```
Splash → Login/Register
  ↓
Register as Engineer → Step 1 (Phone)
  ↓
  OTP Verification → Step 2 (Basic Info)
  ↓
  Bank Account Details → Step 3 (Video KYC)
  ↓
  Aadhaar Card Video → Step 4 (Documents)
  ↓
  Upload 10th, 12th, ITI → Submit Registration
  ↓
  Registration Pending Screen
  ↓
  [Admin verifies KYC + documents]
  ↓
  Notification: "KYC Approved"
  ↓
  Training Schedule Screen
  ↓
  [Engineer attends training]
  ↓
  [Mark Training Complete]
  ↓
  Dashboard (access to jobs)
```

### Main Flow (After Training)

```
Dashboard → Job Dashboard
  ├─ Available Jobs → Job Details → [Accept] → Live Navigation → Checklist → Service Report → Submit to Customer
  ├─ Assigned Jobs (in progress)
  ├─ Completed Jobs (history)
  └─ Earnings Card → Earnings Dashboard

Side Menu:
  ├─ Dashboard
  ├─ Profile (view/edit)
  ├─ Earnings
  └─ Logout
```

### Key Screen Details

**Job Dashboard:**
- Real-time updates via WebSocket
- 4 tabs: Available, Assigned, In Progress, Completed
- List view with: location, fault type, priority, SLA timer
- Pull-to-refresh, infinite scroll

**Job Details:**
- Customer name, location, charger details
- Fault type, SLA remaining (red if <1 hour)
- Applicable checklist template shown
- [Accept] or [Reject] buttons

**Live Navigation:**
- Google Maps showing charger location
- Real-time engineer location (GPS every 10 sec)
- ETA updates
- [Call Customer], [Start Service] buttons

**Checklist Screen:**
- Dynamic items from template
- Each item: task description, input field, [Add Photo], [Add Video]
- Photo gallery inline
- Submit button

**Service Report:**
- Work description textarea
- Spare parts multi-select
- Before/After photos (required)
- Customer e-signature pad
- [Submit] uploads to customer for approval

**Earnings Dashboard:**
- Graphs: Daily, Weekly, Monthly
- Total balance, recent earnings table
- [Request Payout] dialog

---

## Backend APIs

### Base URL
```
https://chargehero-api.com/api/v1
```

### Auth Domain Endpoints

```http
-- Self-registration
POST /auth/register
  Input: { phone, email, name, dob }
  Output: { registration_id, status, otp_sent }

POST /auth/register/verify-otp
  Input: { phone, otp }
  Output: { registration_id, status }

POST /auth/register/submit-kyc
  Input: { video_file, aadhaar_number, captured_photo }
  Output: { registration_id, status }

POST /auth/register/submit-documents
  Input: { doc_10th, doc_12th, doc_iti }
  Output: { registration_id, status }

-- Login (existing users)
POST /auth/login
  Input: { phone }
  Output: { otp_sent: true }

POST /auth/verify-login-otp
  Input: { phone, otp }
  Output: { jwt_token, user_id, role, training_completed }

-- Current user
GET /auth/me
  Output: { user, engineer_profile, training_status }

PUT /auth/me
  Input: { name, email, phone, ... }
  Output: { user }

POST /auth/logout

GET /auth/registration-status
  Output: { status, kyc_approved, training_assigned, training_completed }
```

### Jobs & Dispatch Endpoints

```http
-- Nearby jobs
GET /jobs/nearby?lat=28.7041&lon=77.1025&radius_km=15
  Output: { jobs: [...], total_count }

-- Job management
GET /jobs/assigned
  Output: { jobs: [...] }

GET /jobs/{ticket_id}
  Output: { ticket, charger, customer, checklist_template }

POST /jobs/{ticket_id}/accept
  Output: { ticket_id, status, accepted_at }

POST /jobs/{ticket_id}/reject
  Input: { reason? }
  Output: { ticket_id, status }

POST /jobs/{ticket_id}/start
  Output: { ticket_id, status, timer_started_at }

POST /jobs/{ticket_id}/complete
  Output: { ticket_id, status }

-- Checklists
GET /checklists/templates?charger_id={id}&ticket_type=preventive_maintenance
  Output: { template_id, name, items: [...] }

POST /checklists/{template_id}/start
  Input: { ticket_id, engineer_id }
  Output: { checklist_response_id, status }

POST /checklists/{checklist_response_id}/item/{item_id}/respond
  Input: { response_value, passed, notes, photo?, video? }
  Output: { item_response_id, status, media_urls }

POST /checklists/{checklist_response_id}/submit
  Output: { checklist_response_id, status, submitted_to_customer_at }

-- Service reports
POST /service-reports/{ticket_id}
  Input: { work_description, spare_parts, photos, signature }
  Output: { report_id, status }

GET /service-reports/{ticket_id}
  Output: { report_id, work_description, ... }

-- File upload (S3 pre-signed URL)
POST /attachments/upload
  Input: { file_type, file_size }
  Output: { presigned_url, upload_id }
```

### Copilot Endpoints

```http
-- AI diagnosis
POST /ai/diagnose
  Input: { ticket_id, fault_description, charger_brand, charger_model }
  Output: { diagnosis, root_cause, test_procedure, spare_parts, safety_sop, confidence }

-- General Q&A
POST /ai/ask
  Input: { question, context? }
  Output: { answer, references }

-- Predictions
GET /predictions/{charger_id}
  Output: { predictions: [...] }

POST /predictions/{prediction_id}/acknowledge
  Output: { prediction_id, acknowledged_at }
```

### Notifications Endpoints

```http
GET /notifications
  Output: { notifications: [...] }

PUT /notifications/{id}/read
  Output: { notification_id, is_read }

PUT /notifications/preferences
  Input: { push_enabled, sms_enabled, email_enabled, quiet_hours_start, quiet_hours_end }
  Output: { preferences }
```

### Earnings Endpoints

```http
GET /earnings/summary?period=daily|weekly|monthly
  Output: { period, total_earned, jobs_completed, breakdown: [...] }

GET /earnings/history
  Output: { earnings: [...] }

POST /earnings/request-payout
  Input: { amount, method: 'upi'|'bank' }
  Output: { payout_id, status }

GET /payouts
  Output: { payouts: [...] }
```

### Admin Endpoints (Brief)

```http
GET /admin/engineers
  Output: { engineers: [...], total_count }

GET /admin/engineers/{id}/registration
  Output: { registration_details, kyc_status, documents }

PUT /admin/engineers/{id}/kyc/approve
  Output: { engineer_id, status }

PUT /admin/engineers/{id}/kyc/reject
  Input: { reason }
  Output: { engineer_id, status }

POST /admin/training/assign
  Input: { engineer_id, training_start_date, training_end_date, location }
  Output: { training_id, status }

GET /admin/dashboard/kpis
  Output: { revenue, sla_percent, mttr, mtbf }
```

### Authentication & Authorization

- **JWT Tokens:** Issued after successful login/registration
- **Token Lifetime:** 7 days (refresh token for extension)
- **RBAC Roles:** `engineer`, `customer`, `admin`
- **Header:** `Authorization: Bearer <jwt_token>`

### Error Handling

All errors follow this format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Phone number must be 10 digits",
    "details": { "field": "phone", "reason": "invalid_format" }
  }
}
```

Common codes: `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`

---

## Real-time Features & Deployment

### Real-time Subscriptions (Supabase Realtime)

```
Job Assignment:
  Engineer's app subscribes to: jobs_dispatch_assignments WHERE engineer_id = current_user
  Event: New job assigned → notification appears, job dashboard refreshes

Live Tracking:
  Customer's app subscribes to: jobs_dispatch_assignments WHERE ticket_id = selected_ticket
  Engineer sends GPS every 10 seconds → customer sees live location on map

Checklist Approval:
  Engineer's app subscribes to: jobs_checklist_responses WHERE engineer_id = current_user
  Customer approves checklist → engineer notified in real-time, status updates

Notifications:
  User app subscribes to: notifications_notifications WHERE user_id = current_user
  Any event triggers push + in-app notification
```

### Push Notifications (Firebase Cloud Messaging)

```
Events that trigger notifications:
  - Job assigned: "New job near you: [Charger Brand] at [Location]"
  - Job accepted: Customer: "Engineer [Name] accepted your service request"
  - Checklist submitted: Customer: "Please review checklist and approve"
  - Checklist approved: Engineer: "Customer approved your service report"
  - KYC approved: Engineer: "Your KYC is approved, training dates assigned"
  - Training assigned: Engineer: "[Date]: Training at [Location]"
  - Payment received: Engineer: "Payout of ₹[Amount] received"
```

### Deployment Architecture

```
Frontend (Flutter Android)
  └─ Deployed to: Google Play Store

Backend (FastAPI)
  ├─ Hosting: Render.com (free tier, then paid)
  ├─ Auto-deploy from GitHub (push to main branch)
  ├─ Python 3.10+, Uvicorn, FastAPI
  └─ Environment variables: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, TWILIO_KEY, etc.

Database (PostgreSQL)
  ├─ Hosting: Supabase (free tier: 500MB, scales)
  ├─ Includes: Auth, Realtime, PostGIS extension
  └─ Backups: Automatic daily

Storage (Files & Media)
  ├─ Images (KYC photos, service photos): Supabase Storage (S3-compatible)
  ├─ Videos (KYC video, checklist videos): Supabase Storage or S3
  ├─ Documents (certificates, reports): Supabase Storage
  └─ Access: Pre-signed URLs, S3 upload directly from app

External Services
  ├─ OTP/SMS: Twilio or AWS SNS
  ├─ Push Notifications: Firebase Cloud Messaging (FCM)
  ├─ Email: SendGrid or AWS SES
  ├─ Maps: Google Maps SDK
  ├─ AI/LLM: Claude API (Anthropic)
  └─ Monitoring: Sentry (error tracking) + Render built-in logs
```

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend (Engineer App)** | Flutter (Dart) | Cross-platform, real-time capable, fast development |
| **State Management** | Provider | Lightweight, official recommendation, scales from MVP to complex apps |
| **Maps & Location** | Google Maps SDK | Industry standard, excellent routing, traffic, live tracking |
| **Camera & Video** | camera, video_player plugins | Native integration, liveness detection capable |
| **Signature Capture** | signature_pad | Industry standard e-signature |
| **Backend** | FastAPI (Python) | Async, fast, excellent for AI integration (Claude API), easy scaling |
| **Database** | PostgreSQL (Supabase) | ACID guarantees, PostGIS for location queries, Realtime subscriptions |
| **Authentication** | Supabase Auth + JWT | Secure, extensible with custom claims for RBAC |
| **Real-time** | Supabase Realtime | WebSocket subscriptions, integrated with Postgres |
| **File Storage** | Supabase Storage / S3 | Integrated with auth, pre-signed URLs for direct uploads |
| **Push Notifications** | Firebase Cloud Messaging | Free tier, reliable, integrates with Flutter |
| **AI/LLM** | Claude API (Anthropic) | Excellent for fault diagnosis, knowledge base queries, cost-effective |
| **SMS/OTP** | Twilio or AWS SNS | Reliable, global coverage |
| **Deployment** | Render.com or Railway | Free tier, simple CI/CD, scales easily |
| **Monitoring** | Sentry + Render logs | Error tracking, debugging |
| **Analytics** | Supabase dashboard + custom queries | Built-in analytics, flexible |

---

## Customer App & Admin Portal (Overview)

### Customer App (~35 Screens)

**Key Flows:**
- Login / Register
- Dashboard: Charger status, pending services, alerts
- Raise Ticket: Select charger, describe fault, set priority
- Live Tracking: Watch engineer approach, see ETA
- Service In Progress: See checklist items in real-time (optional transparency)
- Checklist Approval: Review engineer's checklist, approve or request changes
- Service History: Past tickets, service reports, ratings, invoices
- Payments & Invoices: View charges, download invoices
- Profile & Settings
- Notifications

**Key Features:**
- Real-time engineer tracking on map
- Checklist approval workflow
- Photo gallery for service evidence
- Rating system (after service completion)
- AMC management (if applicable)

### Admin Portal (Web-based, ~50 Screens)

**Key Dashboards:**
- **Executive Dashboard:** Revenue (daily/monthly), SLA compliance %, MTTR, MTBF, engineer utilization
- **Engineer Management:** List all engineers, filter by status (kyc_pending, kyc_approved, training_assigned, active), view registration details, approve/reject KYC, assign training
- **Dispatch Center:** Real-time ticket queue, engineer heatmap, manual dispatch option, SLA alerts
- **Training Management:** Create training schedules, assign engineers, mark completion, issue certifications
- **Checklist Templates:** CRUD for preventive maintenance, commission, and issue checklists
- **Analytics:** Charts (daily/monthly revenue, SLA trends, engineer ratings), export reports
- **Notifications:** Send test notifications, view delivery logs, manage notification preferences
- **Settings:** Company config, payment settings, API keys, integrations

**Key Features:**
- Real-time KPI updates
- Bulk operations (assign training to multiple engineers)
- Search & filter (by engineer name, status, location, charger type)
- Export to CSV/PDF (for reporting)

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Backend:**
- [ ] Supabase setup, schema creation, migrations
- [ ] FastAPI project scaffold with domain structure
- [ ] Auth domain: Registration, OTP, JWT
- [ ] Database seeding (charger brands/models, checklist templates)

**Frontend (Engineer App):**
- [ ] Flutter project scaffold with Provider
- [ ] Splash, Login/Register screens (Steps 1-4)
- [ ] Registration form validation
- [ ] KYC video capture + liveness detection
- [ ] Document upload UI

### Phase 2: Core Job Dispatch (Weeks 3-4)

**Backend:**
- [ ] Jobs & Dispatch domain: Ticket CRUD, dispatch algorithm
- [ ] Real-time subscriptions (Supabase Realtime)
- [ ] Notification domain: FCM integration
- [ ] Google Maps API integration (geocoding, routing)

**Frontend (Engineer App):**
- [ ] Training Schedule screen
- [ ] Dashboard & Job Dashboard screens
- [ ] Job Details, Live Navigation screens
- [ ] Real-time job updates (WebSocket)
- [ ] Map integration

### Phase 3: Checklists & Service Completion (Weeks 4-5)

**Backend:**
- [ ] Checklist domain: Templates, item responses, media upload
- [ ] S3/Supabase Storage integration for photos/videos
- [ ] Service report submission

**Frontend (Engineer App):**
- [ ] Checklist screen (dynamic rendering, photo/video capture)
- [ ] Service Report screen (signature, photos, submit)
- [ ] Earnings Dashboard screen

**Customer App (Parallel):**
- [ ] Start building: Login, Dashboard, Raise Ticket screens

### Phase 4: AI Copilot & Polish (Weeks 5-6)

**Backend:**
- [ ] Copilot domain: Claude API integration, knowledge base
- [ ] Diagnostic endpoint
- [ ] Predictive maintenance (basic)

**Frontend (Engineer App):**
- [ ] AI Copilot chat interface
- [ ] Testing, bug fixes, performance optimization

**Admin Portal (Parallel):**
- [ ] Start building: Engineer management, dispatch center, KPIs

### Phase 5: Testing & Deployment (Weeks 6-8)

- [ ] End-to-end testing (all flows)
- [ ] Security audit (JWT, RBAC, data validation)
- [ ] Performance testing (load test dispatch algorithm, real-time subscriptions)
- [ ] Deploy to Render/Railway (free tier)
- [ ] Deploy Flutter app to Google Play Store (alpha/beta)
- [ ] Customer App completion
- [ ] Admin Portal completion
- [ ] Production hardening (monitoring, error handling, logging)

---

## Success Criteria

### MVP Success (Engineer App)

- [ ] Engineers can self-register with video KYC + document upload
- [ ] Admin can verify KYC and assign training dates
- [ ] Engineers receive real-time job assignments based on location & skills
- [ ] Engineers can complete job workflow: navigate → fill checklist → submit report
- [ ] Customers receive notifications and can approve checklists
- [ ] Checklists support PM, Commission, and Issue types with photos/video
- [ ] All data is real-time synced via WebSocket
- [ ] Earnings tracked and displayed accurately
- [ ] No critical bugs in end-to-end flow
- [ ] Deployment to free tier (Supabase + Render) with <5 second API latency

### Performance Targets

- [ ] App startup: <3 seconds
- [ ] Job dashboard load: <2 seconds
- [ ] Real-time updates: <500ms latency
- [ ] File upload (photos): <5 seconds (1-2 MB)
- [ ] Database query (nearby jobs): <1 second

### Security & Compliance

- [ ] JWT authentication enforced on all endpoints
- [ ] RBAC implemented (engineer, customer, admin roles)
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive data
- [ ] API rate limiting (prevent abuse)
- [ ] Data encryption at rest (Supabase default)
- [ ] HTTPS enforced (Render default)

---

## Open Questions & Future Enhancements

### Phase 2 (Training Academy)

- [ ] Course creation & management
- [ ] Video hosting (YouTube, Vimeo, or custom?)
- [ ] Quiz & assessment system
- [ ] Certification issuance & tracking
- [ ] Progress tracking per engineer

### Phase 3 (Spare Parts Marketplace)

- [ ] Inventory management (spare parts catalog)
- [ ] Orders & fulfillment
- [ ] Billing integration

### Phase 4 (Advanced AI)

- [ ] Predictive maintenance (ML models for failure prediction)
- [ ] Knowledge base optimization (embeddings, semantic search)
- [ ] Custom LLM fine-tuning on ChargeHero domain data

### Multi-language & Localization

- [ ] Hindi, Tamil, Telugu, Kannada support
- [ ] Locale-specific formatting (currency, dates, phone)

### OEM Integrations

- [ ] ABB, Delta, Exicom API integrations
- [ ] Telemetry sync (charger status, errors, usage)
- [ ] Predictive maintenance from OEM data

---

## Appendix: Quick Reference

### Database Relationships

```
auth_users
  ├─ auth_engineer_profiles (1:1)
  ├─ auth_customer_profiles (1:1)
  ├─ auth_engineer_skills (1:M)
  ├─ jobs_earnings (1:M)
  ├─ shared_activity_log (1:M)
  └─ notifications_notifications (1:M)

auth_engineer_registrations
  ├─ auth_engineer_kyc (1:1)
  ├─ auth_engineer_documents (1:M)
  └─ auth_engineer_training (1:1)

jobs_chargers
  ├─ jobs_tickets (1:M)
  └─ copilot_predictions (1:M)

jobs_tickets
  ├─ jobs_dispatch_assignments (1:1)
  ├─ jobs_service_reports (1:1)
  ├─ jobs_checklist_responses (1:M)
  ├─ jobs_ticket_attachments (1:M)
  ├─ copilot_diagnostics (1:M)
  └─ jobs_earnings (1:M)

jobs_checklist_templates
  ├─ jobs_checklist_items (1:M)
  └─ jobs_checklist_responses (1:M)

jobs_checklist_responses
  └─ jobs_checklist_item_responses (1:M)

jobs_checklist_item_responses
  └─ jobs_checklist_item_media (1:M)
```

### Key Environment Variables

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
FIREBASE_API_KEY=...
GOOGLE_MAPS_API_KEY=...
JWT_SECRET=random-secret-key
```

### Deployment Checklist

- [ ] Supabase project created & schema deployed
- [ ] FastAPI backend running on Render/Railway
- [ ] Environment variables configured
- [ ] Firebase project created for FCM
- [ ] Google Maps API enabled
- [ ] Claude API key configured
- [ ] Twilio account set up for OTP
- [ ] S3 or Supabase Storage configured
- [ ] DNS/domain configured
- [ ] SSL certificate enabled (auto with Render)
- [ ] Monitoring & alerting configured
- [ ] Backup strategy in place

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-08 | Claude (AI) | Initial design document |

---

**End of Document**
