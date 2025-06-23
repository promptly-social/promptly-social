-- Migration: Refactor social connections authentication data
-- Move access_token, refresh_token, expires_at, and scope into connection_data JSON
-- This provides better flexibility for different authentication methods

-- First, migrate existing data to connection_data JSON field
UPDATE social_connections 
SET connection_data = COALESCE(connection_data, '{}'::jsonb) || 
    jsonb_build_object(
        'access_token', access_token,
        'refresh_token', refresh_token,
        'expires_at', expires_at::text,
        'scope', scope,
        'auth_method', COALESCE((connection_data->>'auth_method'), 'native')
    )
WHERE access_token IS NOT NULL OR refresh_token IS NOT NULL OR expires_at IS NOT NULL OR scope IS NOT NULL;

-- Update any existing Unipile connections to have proper structure
UPDATE social_connections 
SET connection_data = connection_data || 
    jsonb_build_object(
        'auth_method', 'unipile',
        'account_id', access_token  -- For Unipile, access_token was storing account_id
    )
WHERE connection_data->>'auth_method' = 'unipile' OR 
      (connection_data->>'unipile_account_id' IS NOT NULL);

-- Now drop the old columns
ALTER TABLE social_connections 
DROP COLUMN IF EXISTS access_token,
DROP COLUMN IF EXISTS refresh_token,
DROP COLUMN IF EXISTS expires_at,
DROP COLUMN IF EXISTS scope;

-- Add comments to document the new structure
COMMENT ON COLUMN social_connections.connection_data IS 
'JSON field containing authentication data. Structure varies by auth method:
- Native LinkedIn: {"auth_method": "native", "access_token": "...", "refresh_token": "...", "expires_at": "...", "scope": "...", "linkedin_user_id": "...", "email": "..."}
- Unipile: {"auth_method": "unipile", "account_id": "...", "unipile_account_id": "...", "provider": "...", "status": "..."}'; 