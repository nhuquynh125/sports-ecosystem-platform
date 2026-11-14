-- Executed once, on first initialisation of the PostgreSQL data volume.
-- btree_gist : required by the EXCLUDE USING gist constraint that prevents
--              overlapping bookings for the same court (see docs/02-ERD.md).
-- citext     : case-insensitive text for unique emails / usernames.
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS citext;
