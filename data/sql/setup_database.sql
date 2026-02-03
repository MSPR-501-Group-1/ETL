-- =========================================================
-- Complete Database Setup Script for HealthAI Coach
-- Execute this file to create the full database structure
-- =========================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone for consistent timestamps
SET timezone = 'UTC';

-- Create schema if needed (optional, uses public by default)
-- CREATE SCHEMA IF NOT EXISTS healthai_coach;
-- SET search_path TO healthai_coach;

-- Execute all setup scripts in order
\echo 'Creating database tables...'
\i 01_create_tables.sql

\echo 'Creating performance indexes...'
\i 02_indexes.sql

\echo 'Adding business constraints...'
\i 03_constraints.sql

\echo 'Inserting initial reference data...'
\i 04_initial_data.sql

\echo 'Creating useful views...'
\i 05_views.sql

-- Grant permissions for application user
-- Uncomment and modify as needed for your environment
/*
CREATE USER healthai_app WITH PASSWORD 'your_secure_password';

GRANT CONNECT ON DATABASE healthai_coach TO healthai_app;
GRANT USAGE ON SCHEMA public TO healthai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO healthai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO healthai_app;
GRANT SELECT ON ALL VIEWS IN SCHEMA public TO healthai_app;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO healthai_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT USAGE, SELECT ON SEQUENCES TO healthai_app;
*/

-- Verify installation
\echo 'Verifying installation...'

SELECT 'Tables created: ' || count(*) 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

SELECT 'Views created: ' || count(*) 
FROM information_schema.views 
WHERE table_schema = 'public';

SELECT 'Indexes created: ' || count(*) 
FROM pg_indexes 
WHERE schemaname = 'public';

\echo 'Database setup completed successfully!'
\echo 'You can now:'
\echo '1. Load your ETL processed data'
\echo '2. Connect your API application'
\echo '3. Start building your dashboard'