-- PostgreSQL Initialization Script for Signate SaaS Platform
-- Multi-tenant database setup with proper schemas and permissions

-- Create additional databases if specified in POSTGRES_MULTIPLE_DATABASES
DO $$
DECLARE
    db_name TEXT;
    db_list TEXT := COALESCE(getenv('POSTGRES_MULTIPLE_DATABASES'), '');
BEGIN
    -- Only proceed if POSTGRES_MULTIPLE_DATABASES is set
    IF db_list != '' THEN
        -- Split the database list and create each database
        FOR db_name IN SELECT unnest(string_to_array(db_list, ','))
        LOOP
            db_name := trim(db_name);
            IF db_name != '' THEN
                -- Check if database already exists
                IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = db_name) THEN
                    EXECUTE format('CREATE DATABASE %I', db_name);
                    RAISE NOTICE 'Created database: %', db_name;
                ELSE
                    RAISE NOTICE 'Database already exists: %', db_name;
                END IF;
            END IF;
        END LOOP;
    END IF;
END $$;

-- Connect to the main database and set up extensions
\c ${POSTGRES_DB}

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "hstore";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create custom schemas for multi-tenant architecture
CREATE SCHEMA IF NOT EXISTS shared;
CREATE SCHEMA IF NOT EXISTS tenant_template;

-- Grant permissions on schemas
GRANT USAGE ON SCHEMA shared TO ${POSTGRES_USER};
GRANT USAGE ON SCHEMA tenant_template TO ${POSTGRES_USER};
GRANT CREATE ON SCHEMA shared TO ${POSTGRES_USER};
GRANT CREATE ON SCHEMA tenant_template TO ${POSTGRES_USER};

-- Create shared tables for system-wide data
CREATE TABLE IF NOT EXISTS shared.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_name VARCHAR(63) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(63) NOT NULL UNIQUE,
    domain VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shared.tenant_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.tenants(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, key)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tenants_subdomain ON shared.tenants(subdomain);
CREATE INDEX IF NOT EXISTS idx_tenants_active ON shared.tenants(is_active);
CREATE INDEX IF NOT EXISTS idx_tenant_settings_tenant_key ON shared.tenant_settings(tenant_id, key);

-- Create template tables for tenant-specific data
CREATE TABLE IF NOT EXISTS tenant_template.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT true,
    is_staff BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    password_hash VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenant_template.displays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    device_id VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    orientation VARCHAR(20) DEFAULT 'landscape',
    resolution_width INTEGER DEFAULT 1920,
    resolution_height INTEGER DEFAULT 1080,
    refresh_interval INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES tenant_template.users(id)
);

CREATE TABLE IF NOT EXISTS tenant_template.content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    url VARCHAR(500),
    duration INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES tenant_template.users(id)
);

CREATE TABLE IF NOT EXISTS tenant_template.playlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    shuffle BOOLEAN DEFAULT false,
    repeat_mode VARCHAR(20) DEFAULT 'loop',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES tenant_template.users(id)
);

CREATE TABLE IF NOT EXISTS tenant_template.playlist_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    playlist_id UUID NOT NULL REFERENCES tenant_template.playlists(id) ON DELETE CASCADE,
    content_id UUID NOT NULL REFERENCES tenant_template.content(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL DEFAULT 0,
    duration_override INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(playlist_id, content_id)
);

CREATE TABLE IF NOT EXISTS tenant_template.display_playlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    display_id UUID NOT NULL REFERENCES tenant_template.displays(id) ON DELETE CASCADE,
    playlist_id UUID NOT NULL REFERENCES tenant_template.playlists(id) ON DELETE CASCADE,
    schedule_start TIMESTAMP WITH TIME ZONE,
    schedule_end TIMESTAMP WITH TIME ZONE,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for tenant template tables
CREATE INDEX IF NOT EXISTS idx_users_email ON tenant_template.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON tenant_template.users(username);
CREATE INDEX IF NOT EXISTS idx_displays_device_id ON tenant_template.displays(device_id);
CREATE INDEX IF NOT EXISTS idx_displays_active ON tenant_template.displays(is_active);
CREATE INDEX IF NOT EXISTS idx_content_type ON tenant_template.content(content_type);
CREATE INDEX IF NOT EXISTS idx_content_active ON tenant_template.content(is_active);
CREATE INDEX IF NOT EXISTS idx_content_tags ON tenant_template.content USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_playlists_active ON tenant_template.playlists(is_active);
CREATE INDEX IF NOT EXISTS idx_playlist_content_order ON tenant_template.playlist_content(playlist_id, order_index);

-- Function to create a new tenant schema
CREATE OR REPLACE FUNCTION shared.create_tenant_schema(tenant_schema_name TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    table_record RECORD;
BEGIN
    -- Create the schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', tenant_schema_name);

    -- Grant usage to the application user
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I', tenant_schema_name, current_user);
    EXECUTE format('GRANT CREATE ON SCHEMA %I TO %I', tenant_schema_name, current_user);

    -- Copy all tables from template schema
    FOR table_record IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'tenant_template'
    LOOP
        EXECUTE format('CREATE TABLE %I.%I (LIKE tenant_template.%I INCLUDING ALL)',
                      tenant_schema_name, table_record.tablename, table_record.tablename);
    END LOOP;

    -- Copy foreign key constraints
    FOR table_record IN
        SELECT conname,
               pg_get_constraintdef(c.oid) as condef
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = 'tenant_template'
        AND c.contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE %I.%I ADD CONSTRAINT %I %s',
                      tenant_schema_name,
                      (SELECT tablename FROM pg_tables WHERE schemaname = 'tenant_template' LIMIT 1),
                      table_record.conname,
                      replace(table_record.condef, 'tenant_template.', tenant_schema_name || '.'));
    END LOOP;

    RETURN TRUE;

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error creating tenant schema %: %', tenant_schema_name, SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to drop a tenant schema
CREATE OR REPLACE FUNCTION shared.drop_tenant_schema(tenant_schema_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    EXECUTE format('DROP SCHEMA IF EXISTS %I CASCADE', tenant_schema_name);
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error dropping tenant schema %: %', tenant_schema_name, SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Create trigger function for updating timestamps
CREATE OR REPLACE FUNCTION shared.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for timestamp updates on shared tables
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON shared.tenants
    FOR EACH ROW EXECUTE FUNCTION shared.update_updated_at_column();

CREATE TRIGGER update_tenant_settings_updated_at
    BEFORE UPDATE ON shared.tenant_settings
    FOR EACH ROW EXECUTE FUNCTION shared.update_updated_at_column();

-- Insert default shared data
INSERT INTO shared.tenants (schema_name, name, subdomain) VALUES
    ('tenant1', 'Demo Tenant 1', 'demo1'),
    ('tenant2', 'Demo Tenant 2', 'demo2')
ON CONFLICT (subdomain) DO NOTHING;

-- Create tenant schemas for demo tenants
SELECT shared.create_tenant_schema('tenant1');
SELECT shared.create_tenant_schema('tenant2');

COMMENT ON SCHEMA shared IS 'Shared schema for system-wide multi-tenant data';
COMMENT ON SCHEMA tenant_template IS 'Template schema for tenant-specific table structures';
COMMENT ON FUNCTION shared.create_tenant_schema(TEXT) IS 'Creates a new tenant schema with all necessary tables';
COMMENT ON FUNCTION shared.drop_tenant_schema(TEXT) IS 'Safely drops a tenant schema and all its data';