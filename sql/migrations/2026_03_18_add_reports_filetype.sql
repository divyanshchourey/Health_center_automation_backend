ALTER TABLE Reports
ADD COLUMN IF NOT EXISTS FileType TEXT;

UPDATE Reports
SET FileType = COALESCE(FileType, 'application/pdf')
WHERE FileType IS NULL;
