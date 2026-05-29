-- =============================================================================
-- AmpAware — PostgreSQL initialization script
-- Run once by Docker on first container startup.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- trigram similarity search
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN indexes for range queries
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";  -- query performance tracking

-- Default timezone for this database session
SET timezone = 'UTC';

-- =============================================================================
-- Application schema comments
-- =============================================================================
COMMENT ON DATABASE ampaware IS
  'AmpAware — Industrial smart energy metering platform database';
