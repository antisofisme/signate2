-- Anthias SaaS Platform - PostgreSQL Initialization Script
-- Database setup and optimization for production deployment

-- Create application database and user if they don't exist
DO $$
BEGIN
    -- Create user if it doesn't exist
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anthias') THEN
        CREATE USER anthias WITH PASSWORD 'anthias_secure_password';
    END IF;

    -- Create database if it doesn't exist
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'anthias_production') THEN
        CREATE DATABASE anthias_production OWNER anthias;
    END IF;
END
$$;

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE anthias_production TO anthias;

-- Connect to the application database
\c anthias_production;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO anthias;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anthias;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anthias;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anthias;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anthias;

-- Performance optimizations
-- Increase shared_buffers for better performance
ALTER SYSTEM SET shared_buffers = '256MB';

-- Optimize checkpoint settings
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';

-- Optimize query planner
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Connection settings
ALTER SYSTEM SET max_connections = 200;

-- Logging configuration
ALTER SYSTEM SET log_destination = 'stderr';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Reload configuration
SELECT pg_reload_conf();