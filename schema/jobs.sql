-- Canonical job model. SQLite-flavored; portable to Postgres.
--
--   company            one row per employer
--   job                one row per real opening; many appearances point at one job
--   source_appearance  one row per (source, source_job_id) sighting; raw, never edited
--   analysis           one row per (job, analysis_version, model_version); re-runnable
--   user_state         what Rone did with the card; adjusts ordering, never filters
--   suppression        the rare jobs hidden from the feed, with rule + evidence
--
-- Retrieval writes appearances and resolves them to jobs. It never judges.
-- Analysis reads jobs and writes analysis rows. It never fetches.

CREATE TABLE company (
  id              INTEGER PRIMARY KEY,
  name            TEXT NOT NULL,
  domain          TEXT UNIQUE,
  linkedin_url    TEXT,
  ats_kind        TEXT,                -- greenhouse | lever | ashby | workday | other | NULL
  ats_slug        TEXT,                -- later watchlist; filled opportunistically
  first_seen_at   TEXT NOT NULL
);

CREATE TABLE job (
  id                   INTEGER PRIMARY KEY,
  company_id           INTEGER NOT NULL REFERENCES company(id),
  title                TEXT NOT NULL,
  title_normalized     TEXT NOT NULL,
  location_text        TEXT,
  remote               TEXT,           -- remote | hybrid | onsite | unknown
  apply_url            TEXT,           -- company/ATS application URL when known
  description          TEXT,           -- best (most complete) description seen
  description_hash     TEXT,
  salary_min           INTEGER,
  salary_max           INTEGER,
  salary_currency      TEXT,
  posted_at            TEXT,           -- earliest source-claimed posting date
  first_seen_at        TEXT NOT NULL,  -- when Mo Money first saw any appearance
  first_seen_source    TEXT,           -- which source got there first
  last_seen_at         TEXT NOT NULL,
  closed_at            TEXT,
  reopened_from_job_id INTEGER REFERENCES job(id),
  status               TEXT NOT NULL DEFAULT 'open',  -- open | closed | reopened
  -- Source novelty only. Discovery and attention novelty depend on what Rone
  -- saw elsewhere, which the system can't observe; the bakeoff measures those.
  on_major_boards      TEXT NOT NULL DEFAULT 'unknown' -- yes | no | unknown (LinkedIn/Indeed)
);

CREATE INDEX job_dedupe ON job(company_id, title_normalized);

CREATE TABLE source_appearance (
  id               INTEGER PRIMARY KEY,
  job_id           INTEGER REFERENCES job(id),  -- NULL until resolved
  source           TEXT NOT NULL,     -- theirstack | serpapi_google_jobs | ats_direct | chrome_manual
  source_job_id    TEXT NOT NULL,
  source_url       TEXT,              -- where the source saw it (LinkedIn, Indeed, careers page...)
  original_url     TEXT,              -- company/ATS URL as reported
  retrieval_mode   TEXT NOT NULL,     -- title_family | description_family
  query_family     TEXT,              -- id from search/families.yaml
  query_text       TEXT,              -- exact query sent
  source_posted_at TEXT,
  discovered_at    TEXT,
  fetched_at       TEXT NOT NULL,
  description_len  INTEGER,
  raw_json         TEXT NOT NULL,
  UNIQUE (source, source_job_id)
);

-- Fields mirror analysis/scouting.yaml. Tag fields and note fields are separate
-- columns so a cheaper tag-only pass can be added later without a migration;
-- V1 fills both in one call for every job.
CREATE TABLE analysis (
  id                 INTEGER PRIMARY KEY,
  job_id             INTEGER NOT NULL REFERENCES job(id),
  analysis_version   TEXT NOT NULL,
  model_version      TEXT NOT NULL,
  analyzed_at        TEXT NOT NULL,
  -- tags
  role_family        TEXT,
  overlap            TEXT,            -- strong | partial | weak | very_low
  stretch            TEXT,            -- none | some | big
  stretch_reasons    TEXT,            -- JSON array
  wildcard           INTEGER,         -- 0/1
  ai_relevance       TEXT,            -- central | present | adjacent | none
  client_ownership   TEXT,            -- none | supporting | owns_accounts | unclear
  known_blocker      TEXT,            -- JSON {rule_id, evidence} or NULL; see suppression
  -- scouting note
  why_surfaced       TEXT,
  overlap_points     TEXT,            -- JSON array
  stretch_points     TEXT,            -- JSON array
  caveats            TEXT,            -- JSON array
  worth_opening_because TEXT,
  missing_info       TEXT,            -- JSON array
  confidence         TEXT,            -- high | medium | low
  raw_output         TEXT NOT NULL,
  UNIQUE (job_id, analysis_version, model_version)
);

CREATE TABLE user_state (
  job_id       INTEGER PRIMARY KEY REFERENCES job(id),
  state        TEXT NOT NULL,         -- new | seen | opened | saved | dismissed | applied
  already_seen_elsewhere INTEGER,     -- 0/1, optional tap: "I'd already found this"
  updated_at   TEXT NOT NULL
);

-- Ordering may learn from card-level signals (opened, saved, dismissed, stretch_too_big).
-- 'applied' is recorded for tracking only; NOT applying is never a negative signal
-- (docs/reframe.md amendment 6).
CREATE TABLE user_event (
  id         INTEGER PRIMARY KEY,
  job_id     INTEGER NOT NULL REFERENCES job(id),
  event      TEXT NOT NULL,           -- shown | opened | glad | saved | dismissed | stretch_too_big | applied | unhid
  at         TEXT NOT NULL
);

-- V1 suppresses only: closed jobs, and explicit constraints Rone has declared
-- impossible (config, not model judgment). Suppressed jobs stay queryable.
CREATE TABLE suppression (
  job_id      INTEGER NOT NULL REFERENCES job(id),
  rule_id     TEXT NOT NULL,          -- closed | location_impossible | work_auth | ...
  evidence    TEXT,
  created_at  TEXT NOT NULL,
  overridden  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (job_id, rule_id)
);
