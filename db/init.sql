-- Password Strength Checker: statistics table.
-- Run against the `passcheck` database, e.g.:
--   psql -h <host> -U passcheck -d passcheck -f db/init.sql
-- Creating the database and the `passcheck` user (with the team's private
-- password) is a deployment step and is intentionally NOT done here.
--
-- Privacy: there is deliberately no password column. Only the environment,
-- the strength label and a length bucket are stored.
--   length_bucket values: '1-7', '8-11', '12-15', '16+'
--   label values:         'Weak', 'Medium', 'Strong', 'Very Strong'

CREATE TABLE IF NOT EXISTS stats (
    id            SERIAL PRIMARY KEY,
    env           VARCHAR(32) NOT NULL,
    label         VARCHAR(16) NOT NULL,
    length_bucket VARCHAR(16) NOT NULL,
    ts            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- If this file is run by a superuser (e.g. `sudo -u postgres psql`), let the
-- application user read and insert. Skipped if the role does not exist.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'passcheck') THEN
        GRANT SELECT, INSERT ON stats TO passcheck;
        GRANT USAGE, SELECT ON SEQUENCE stats_id_seq TO passcheck;
    END IF;
END
$$;
