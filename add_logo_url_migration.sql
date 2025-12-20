-- Add logo_url column to radios table
ALTER TABLE radios ADD COLUMN logo_url VARCHAR(500);

-- Add comment
COMMENT ON COLUMN radios.logo_url IS 'URL du logo personnalisé de la radio (optionnel)';
