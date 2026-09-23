-- Canonical job model. SQLite-flavored; portable to Postgres.
--
-- Three layers, kept separate on purpose:
--   source_appearance  one row per (source, source_job_id) sighting. Raw, never edited.
--   job                one row per real opening. Many appearances point at one job.
--   grade              one row per (job, rubric_version, grader_version). Re-gradable.
--
-- Retrieval writes appearances and resolves them to jobs. It never grades.
-- The grader reads jobs and writes grades. It never fetches.

CREATE TABLE company (
  id              INTEGER PRIMARY KEY,
  name            TEXT NOT NULL,
  domain          TEXT UNIQUE,            -- best dedupe key when present
  linkedin_url    TEXT,
  ats_kind        TEXT,                   -- greenhouse | lever | ashby | workday | other | NULL
  ats_slug        TEXT,                   -- feeds the later watchlist; filled opportunistically
  first_seen_at   TEXT NOT NULL
);

CREATE TABLE job (
  id                  INTEGER PRIMARY KEY,
  company_id          INTEGER NOT NULL REFERENCES company(id),
  title               TEXT NOT NULL,
  title_normalized    TEXT NOT NULL,      -- lowercased, seniority/punctuation stripped
  location_text       TEXT,
  remote              TEXT,               -- remote | hybrid | onsite | unknown
  apply_url           TEXT,               -- canonical company/ATS application URL when known
  description         TEXT,               -- best (longest complete) description seen
  description_hash    TEXT,               -- for detecting material edits
  salary_min          INTEGER,
  salary_max          INTEGER,
  salary_currency     TEXT,
  posted_at           TEXT,               -- earliest source-claimed posting date
  first_seen_at       TEXT NOT NULL,      -- when WE first saw any appearance
  last_seen_at        TEXT NOT NULL,      -- most recent appearance still live
  closed_at           TEXT,               -- source-reported or inferred (all appearances gone)
  reopened_from_job_id INTEGER REFERENCES job(id), -- repost after a gap; see DESIGN.md
  status              TEXT NOT NULL DEFAULT 'open'  -- open | closed | reopened
);

CREATE INDEX job_dedupe ON job(company_id, title_normalized);

CREATE TABLE source_appearance (
  id               INTEGER PRIMARY KEY,
  job_id           INTEGER REFERENCES job(id),   -- NULL until resolved
  source           TEXT NOT NULL,     -- theirstack | serpapi_google_jobs | linkedin_alert | ats_direct | chrome_manual
  source_job_id    TEXT NOT NULL,     -- the source's own id
  source_url       TEXT,              -- where the source says it saw it (LinkedIn, Indeed, ...)
  original_url     TEXT,              -- company/ATS URL as reported by the source
  query_family     TEXT,              -- which search family surfaced it (search/families.yaml)
  query_text       TEXT,              -- exact query sent, for recall analysis
  source_posted_at TEXT,
  discovered_at    TEXT,              -- source's own discovery timestamp, if exposed
  fetched_at       TEXT NOT NULL,     -- when we pulled it
  description_len  INTEGER,           -- completeness metric for the bakeoff
  raw_json         TEXT NOT NULL,     -- full payload; lets us re-parse without re-fetching
  UNIQUE (source, source_job_id)
);

CREATE TABLE grade (
  id               INTEGER PRIMARY KEY,
  job_id           INTEGER NOT NULL REFERENCES job(id),
  rubric_version   TEXT NOT NULL,     -- e.g. "v1.0" from rubric/rubric.yaml
  grader_version   TEXT NOT NULL,     -- model id + prompt hash
  graded_at        TEXT NOT NULL,
  gate             TEXT NOT NULL,     -- pass | fail | review
  gate_reasons     TEXT,              -- JSON array of hard-gate hits
  role_family      TEXT,              -- one of search/families.yaml ids, or 'other'
  content_fit      INTEGER,           -- 0-4
  ai_fit           INTEGER,           -- 0-4
  seniority_fit    INTEGER,           -- 0-4
  audience_fit     INTEGER,           -- 0-4
  client_ownership TEXT,              -- none | supporting | owns_accounts | unclear
  red_flags        TEXT,              -- JSON array
  confidence       TEXT,              -- high | medium | low
  missing_evidence TEXT,              -- JSON array: what the posting didn't say
  rank_score       REAL,              -- computed from the fields above, not asked of the model
  reason           TEXT,              -- one line, human-facing
  raw_output       TEXT NOT NULL,
  UNIQUE (job_id, rubric_version, grader_version)
);
