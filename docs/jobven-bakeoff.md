# Jobven vs TheirStack: Bakeoff Results

Run 2026-09-25 (UTC) against Jobven's `GET /v1/public/jobs` on the 7-day trial key. It made 307 calls and used **281 of 2,500 trial jobs**; 2,219 are left. Every call and its delivered-job count is in `bakeoff/raw/jobven_log.jsonl`. The logged total matches the API's `X-RateLimit-Remaining` header exactly (2,500 → 2,219). Raw responses are in `bakeoff/raw/jobven_*.json`, and the docs pages as fetched are in `bakeoff/raw/jobven_docs/`.

| phase | cap | used |
|---|---:|---:|
| API semantics | 50 | 19 |
| known-job recall | 400 | 86 |
| family replay | 1,500 | 176 |
| reserve | ~550 | 0 |

The quality sample reused jobs that had already been delivered, so it pulled nothing extra.

**Bottom line: stay with TheirStack alone.** Jobven found **0 of the 7 glads** and 4 of the 28 other interesting spike jobs (4 of 35 overall). Its whole index holds about 2,000 US remote jobs per week across every profession. Rone's title families plus description phrases pull about **117 unique jobs a week, or ~17 a day**, where TheirStack's Config B pulls ~213 a day. Jobven's data is clean and every apply link goes to the employer. Its per-job quality matches TheirStack's, but the net is roughly 13× smaller. The one open question is the 15 Jobven-only cards below. If Rone marks several of them glad, check whether TheirStack also has those jobs before paying for Jobven next to it (see §8).

## 1. API semantics

These were verified against the live API. Where the docs disagreed, the 2026-09-24 changelog was right every time.

| question | answer | evidence (call ids in `jobven_log.jsonl`) |
|---|---|---|
| Does `q` search title only, or title + description? | **Title only.** It matches whole words in any order, and supports `"phrases"`, `OR` and `-exclusions`. The Dec 2025 launch post ("full text search across titles, descriptions, and skills") is out of date. | `sem_06`: title + a word found only in that job's description returned 0. `sem_07`: that word alone returned 0. `sem_08`: the same word through `descriptionQuery` returned 1. |
| Does `descriptionQuery` accept OR or multiple phrases? | **No. It takes one whole-word phrase only.** `A OR B` and `"A" "B"` are matched as literal text (0 results). A repeated param or `descriptionQuery[]` is rejected with "must be a string". There's no regex, so a TheirStack pattern like `develop(ing)?` has to be split into separate phrases, and `e-learning` only matches that exact spelling. | `sem_09` = 4, `sem_10` = 1, `sem_11` / `sem_12` = 0, `sem_p_descq_repeat` / `sem_p_descq_bracket` = 400 |
| Does `q` OR work? | Yes. `"instructional designer" OR "curriculum developer" OR "learning designer"` returned 2, which equals 1 + 0 + 1. | `sem_13`–`sem_15` |
| Do `q` exclusions work alongside `descriptionQuery`? | Yes. Adding `-"client support"` to "knowledge base" cut the results from 17 to 16. `q` is capped at 200 characters. | `sem_20`, `sem_22` |
| Is there an exclude-IDs or cursor param to avoid re-delivery? | **No.** The API rejects unknown params with a whitelist ("property X should not exist"). `excludeIds`, `idNot`, `exclude` and `ids` were all rejected, as was `companyIds`. `cursor` only pages within a single query. | `sem_p_*` (all free) |
| Is there a count that costs nothing? | **No.** `includeTotal=true` returns an exact `meta.total`, but it needs `limit ≥ 1`, and `limit=0` returns 400. So any count with results costs 1 job. A zero-result count is free. Company lookups (`/v1/public/companies?search=`) are free and show whether an employer is indexed at all. | `sem_p_limit0_total`, `sem_c1`, `sem_c2` |
| Incremental discovery: is there a created, indexed or updated-after filter? | **Not in REST.** `createdAfter`, `updatedAfter`, `indexedAfter`, `firstSeenAfter`, `discoveredAfter` and `since` are all rejected. `sortBy` accepts only `postedAt`, `title` and `company`. The job object has no created or first-seen timestamp. `postedAfter` filters on the date the posting states. The first-seen date is used only when a posting gives no date (changelog 2026-08-28). One recall hit shows the risk: Medtronic's training-specialist job carries `postedAt` 2026-07-21 but first surfaced on TheirStack on 09-23. A strict `postedAfter` watermark would never deliver a job like that if Jobven indexed it late. | `sem_p_createdAfter` … `sem_p_sort_*` |
| Would the `job.created` / `job.updated` webhooks solve it? | **Technically yes, but not at a sane cost.** `job.created` fires for "a job we haven't seen before" (and for a relisted job under its old id), which is a real discovery feed. But webhook filters accept only `remoteType`, `experienceLevel`, `employmentType`, `industry`, `language`, `country`, `state`, `city`, salary, visa and relocation. **They don't accept `q` or `descriptionQuery`.** A US + remote subscription would deliver every new US remote job: ~2,043 a week (≈8,800 a month) plus `job.updated` events, at 1 job each. That nearly fills Starter's 10k. Adding `flexible` (3,339 a week, ≈14,300 a month) needs Growth ($199). Events that arrive over quota are dropped and never re-sent. Starter allows only 1 subscription, and it needs a public HTTPS endpoint. | `sem_16`, `sem_24`; docs `webhooks` |

Other things the next integration needs to know:
- **Always pass `limit`.** When it's omitted, the API returns the tier maximum (changelog 2026-09-18), and each job returned is billed. The trial page size is 25.
- **Cloudflare blocks the default Python-urllib User-Agent** with error 1010 (`sem_00`). Send a custom UA.
- Overview docs show `skills=react` without brackets; the reference requires `skills[]`. The quota headers are documented as "calls" but count jobs.
- Index size, as `meta.total` with `postedAfter` = 7 days: 42,315 jobs worldwide; 24,334 US; **2,043 US + `remoteType=remote`**; 3,339 US remote + flexible. 465,835 jobs are active overall across 5,510 indexed companies.

## 2. Known-job recall (the main test)

Method, per job:
1. A free company lookup.
2. An exact-title `q` search: US, posted since 2026-09-01, any workplace so that Jobven's remote tag can't hide a match, limit 10.
3. Exact title plus a distinctive description phrase from `bakeoff/jobs_sample.jsonl`, checked in both `status=active` and `status=closed`.

For the glads, step 2 was repeated with no country, date or status filter. Returned company names were compared locally. Results are in `bakeoff/jobven_recall.json`.

**Glads: 0 of 7 found.** None of them were found closed either.

| card | company | title | TS posted | employer in Jobven's company index? | Jobven |
|---|---|---|---|---|---|
| #5 | Blue Cross and Blue Shield of NC | Senior Digital Product Analyst | 09-23 | no (only "Alberta Blue Cross") | not found |
| #7 | Citian | Customer Education Specialist | 09-23 | no | not found (same title found at Runway, Samsara, MaintainX) |
| #10 | Accenture (Udacity) | Senior Program Manager - AI Learning Operations | 09-23 | no | not found |
| #12 | Commerce (BigCommerce) | Technical Training Content Developer | 09-19 | no | not found |
| #14 | A.T. Still University | CGHS - Instructional Designer (remote) | 09-22 | no | not found |
| #15 | Shipley Associates | Business Development Course Developer | 09-22 | no | not found |
| #17 | Ladders (client unnamed) | Sr Manager of Curriculum and Instruction | 09-21 | no | not found |

Both description-search wins fail at the index level. BCBS NC and Shipley aren't in Jobven's company list at all, so no query could reach them.

**Other interesting spike jobs: 4 of 28 distinct employers found.**

| company | title | TS posted | Jobven |
|---|---|---|---|
| NICE | Senior Education Professional, Development | 09-23 | **found**, posted 09-22, tagged `flexible`, Greenhouse EU link |
| Medtronic | Principal Field Service Technical Training Specialist | 09-23 | **found**, `postedAt` 07-21, tagged `hybrid`, active (likely a repost on TheirStack's side) |
| White Circle | Content Lead | 09-22 | **found**, posted **09-11**, 11 days before TheirStack saw it |
| AfterQuery | Technical Content Writer (Contract) | 09-21 | **found**, posted 09-21 |
| Arrow Electronics, Fortra | Customer Success Content & Enablement Mgr; Offensive Security Training Content Developer | 09-23 | not found, although both **companies are indexed** (so coverage within a company is partial) |

These 22 employers were not found, and none of them is in the company index:
- Khan Academy, Solera Senior Living, ZipLiens, 440 Strategy, CVS Health, Calculated Hire, Veeva
- Miaplaza, Edgewater, Quizcademy, Lunit, Spectrio, TalentHop, NYC Health + Hospitals, Spring Health
- Horizontal Talent, BJU, UW-Oshkosh, Mometrix, Save the Children, Pittsburgh, Crew

Staffing relistings (Ladders, TalentHop, Horizontal, Calculated Hire) hide the employer, so they can't be traced to a careers page.

**Read:** Jobven reaches roughly 1 in 9 of the jobs Rone cares about from the spike, and none of the ones he marked glad. By the decision frame, 0 of 7 is well below the ~3 of 7 "smaller net" case. The samples are small, but the pattern isn't borderline: most of these employers simply aren't in the index.

## 3. Family replay (US + remote, last 7 days)

- **Title families:** one call per family, `q` = the OR of the quoted titles. Per-family `must_description` can't be expressed as one phrase, so it wasn't applied (it would only shrink these counts further).
- **Description phrases:** one call per phrase, because `descriptionQuery` has no OR. TheirStack regex variants were expanded into 26 literal phrases.
- **Title exclusions:** `TITLE_EXCLUDE` doesn't fit in `q`'s 200 characters, so the 8 highest-volume terms go into `q` as `-"phrase"`: account executive, account manager, sales representative, sales manager, customer service representative, help desk, customer success manager, support specialist. The full regex list was then applied locally.

Every job was paged to completion. Output is in `bakeoff/jobven_family_jobs.jsonl` and `bakeoff/jobven_family_sizes.json`.

| title family | Jobven remote | + flexible | US any workplace | TheirStack (remote, 7-day) |
|---|---:|---:|---:|---:|
| content_dev | 2 | 2 | 7 | 33 |
| instructional_lxd | 2 | 3 | 4 | 46 |
| curriculum_training | 0 | 0 | 0 | 20 |
| enablement_education | 4 | 6 | 10 | 31 |
| technical_content | 2 | 4 | 15 | 29 |
| ai_learning | 1 | 2 | 7 | 127 |
| **union** | **10 unique** (11 deliveries) | 17 | 43 | **276** |

Even with no remote filter, the title families total 43 a week. So the gap is the size of the index, not Jobven's remote classification.

| phrase (family) | Jobven, excl. applied | no excl. | + flexible | TheirStack 7-day (credit-projection §1) |
|---|---:|---:|---:|---:|
| AI adoption (ai_adoption) | 44 | 50 | 57 | 252 |
| enablement content (enablement_material) | 16 | 16 | 17 | 65 |
| knowledge base (knowledge_content) | 15 | 17 | 30 | 510 |
| enablement materials | 10 | 11 | 12 | 143 |
| customer training | 7 | 8 | 12 | 180 |
| customer education | 6 | 7 | 8 | 84 |
| learning content | 5 | 5 | 7 | 93 |
| curriculum development | 4 | 4 | 4 | 116 |
| content operations / content governance | 3 / 3 | 3 / 3 | 3 / 3 | 40 / 31 |
| help center content | 2 | 2 | 2 | 13 |
| AI literacy | 2 | 2 | 5 | 43 |
| course development | 1 | 1 | 2 | 38 |
| playbooks and training / onboarding content / academy content | 1 / 1 / 1 | same | same | 3 / 5 / 2 |
| training curriculum | 0 | 2 | 3 | 75 |
| develop(ing) course content, e-learning content, design(ing) (the) curriculum ×4, AI training program, teach teams to use AI | 0 | 0 | 0 | 0-10 each |
| **all 26 phrases** | **121 deliveries, 110 unique** | 134 | 168 | 1,569 (1,283 with exclusions) |

- **Daily union:** 117 unique jobs a week (10 title + 110 description − 3 in both).
  - By posted date: 09-18 17 · 09-19 1 · 09-20 0 · 09-21 29 · 09-22 27 · 09-23 23 · 09-24 20.
  - That's ~17 a day on average, and ~24 on a weekday.
- **Re-delivery from one call per phrase:** 11 of 110 description jobs matched 2-3 phrases. Together with the 3 title/description overlaps, that's 15 extra deliveries on 132 (**+13%**).
- **Exclusions:** the in-`q` exclusions removed 13 jobs server-side (134 → 121). The full local `TITLE_EXCLUDE` would drop 9 more that were already paid for:
  - 5 tech_support
  - 2 cust_success
  - 2 presales_eng
- **Interesting yield:** ~18 of the 117, or ~2.5 a day.
  - Title families: 6 of 10.
  - Description phrases: 12 of 107, read from titles and summaries plus full reads of the 30 sampled.
  - TheirStack's projection is ~45-50 interesting a day.
- **Only-path wins:** Wiz came only through bare "knowledge base", and ServiceNow Community Web Manager only through "content governance".

## 4. Quality: 60 delivered jobs, stratified 30 title / 30 description

**Sample:**
- **Title stratum (30):** all 10 title-family jobs, plus 20 seeded-random title-search hits from the recall phase. These are title searches for content/learning titles in the US with any workplace.
- **Description stratum (30):** seeded-random from the 107 description-only jobs.

**Method:** scouting labels were hand-run on the `analysis/scouting.yaml` v0.2-draft rubric, including the Maryland state-allowlist rule. They're in `bakeoff/jobven_scouting_analysis.jsonl`, and metrics are in `bakeoff/jobven_metrics.json`.

| metric | Jobven | TheirStack spike |
|---|---|---|
| interesting, title stratum | 9 of 30 (30%); 6 of 10 (60%) in the US-remote title replay | 62% |
| interesting, description stratum | 3 of 30 (10%) | 12% |
| remote tag vs posting text (jobs tagged remote) | 48 tagged remote. Text says remote 17 (35%), unclear 25 (52%), field territory with travel 6 (13%), onsite 0 | 143 tagged remote. Text: remote 48%, unclear 28%, field 14%, onsite 9%, hybrid 1% |
| non-remote tags | all 10 onsite/hybrid tags agree with the text | n/a (TheirStack was filtered to remote) |
| state-restricted "remote" jobs | 3 in the sample (VA, OH and ME teachers; home-state required), plus 1 outside it (Vynca Care: its "following states" list omits MD) | 2 missed at first (Springboard, Bryan U), caught by the allowlist rule |
| description length | min 2,392, median 6,376, p90 10,892, 0 under 1,000 | min 1,552, median 5,944, p90 10,059 |
| description markup | **22 of 190 (12%) contain raw HTML tags** inside the text (double-encoded ATS markup; 6 of 60 in the sample). Strip it before analysis. | clean markdown |
| direct employer/ATS apply URL | **190 of 190 (100%)**, and 0 go through LinkedIn/Indeed. 4 go through a staffing ATS (JobDiva) or a recruiter's Ashby board. | 41% |
| staffing / recruiter share | 5 of 60 (8%) in the sample; 7 of 190 (4%) overall (Diverse Lynx, Highlight Talent, Truelogic) | 19% |
| duplicates (same company + description, different id) | 3 of 60 in the sample; **15 of 190 (7.9%)** overall. Mostly one requisition posted once per city (ServiceNow ×5, ×3, ×2; CrowdStrike regions ×3; MaintainX ×2). Also Experian's director role appears under 2 ids. | 5.6% |
| salary present | 104 of 190 (55%) | 27% |
| title mislabels | 1 ("Technical Writer" at Diverse Lynx is a data-center project manager) | several wrong structured fields |

Jobven's per-job quality is as good as TheirStack's or better: employer links, salary, less staffing noise. Its remote tag is at least as loose, with only 35% of remote-tagged jobs saying remote in the text, so the scouting pass still has to read the posting. Dedupe needs a company + description hash, which the design already assumes.

## 5. Overlap with TheirStack

This compares 22 interesting Jobven jobs against all 178 jobs in TheirStack's raw spike and projection responses. The match is on title and company. The TheirStack raw files are a small sample of its ~1,500 jobs a week, so "not in the spike" is an upper bound on novelty, not proof of it.

| | count |
|---|---:|
| interesting Jobven jobs, from reads plus title/summary triage | 22 (+ NICE and Medtronic from recall) |
| also in the TheirStack spike raw data | **6**: AfterQuery, White Circle, NICE, Runway, Roboflow, Experian (the last three were in TheirStack's `limit: 1` sizing samples) |
| not seen in the TheirStack spike | **17** (15 are carded below; Directive Consulting and Ironclad aren't) |

Six overlaps turning up in a sample that small suggests TheirStack's full index holds a good share of the other 17 too. They're ordinary Ashby, Greenhouse and Workday postings, which TheirStack also scrapes.

## 6. Projected monthly cost for an equivalent-breadth config

The config mirrors TheirStack's Config B, run daily: 6 title-family calls + 26 phrase calls, US + remote, exclusions in `q`, full `TITLE_EXCLUDE` applied locally.

| item | jobs/month |
|---|---:|
| unique jobs (117 a week ÷ 7 × 30) | ~500 |
| + per-phrase re-delivery (+13%) | ~570 |
| strict daily watermark (`postedAfter` = last run) | **~570** (misses late-indexed jobs; see §1) |
| 3-day re-pull window to catch late indexing | ~1,700 |
| 7-day re-pull window | ~4,000 |
| + `flexible` jobs (×1.4) | up to ~5,600 |
| alternative: `job.created` webhook, US + remote, no text filter | ~8,800 + updates (≈ Starter cap); with flexible ~14,300 → Growth |

- **Jobven cost:** every REST variant fits **Starter at $79/mo**. The free plan (300/mo) is too small. Analysis adds ~$3-16/mo at the spike's per-job estimates.
- **Jobven instead of TheirStack:** $79/mo for ~17 cards and ~2.5 interesting a day, against ~213 cards and ~45-50 interesting a day for $169.
- **Jobven alongside TheirStack:** $248/mo. It adds ~17 cards a day, of which ~2 are interesting and not known to be on TheirStack already.

## 7. Jobven-only sample cards: please mark "glad I saw this"

These are 15 interesting, non-suppressed jobs that weren't seen in TheirStack's spike data. Jobven only records the employer source, so the cards can't say whether a job is also on LinkedIn or Indeed; there's no OFF MAJOR BOARDS tag. Marks go in `bakeoff/jobven_cards_marks.csv`, or reply with card numbers.

### J1. Lead Instructional Designer at Neon One (listed by Highlight Talent)
`STRONG OVERLAP · BIG STRETCH` · overlap **strong** · stretch **big** · AI adjacent · salary not stated · posted 2026-09-24
- **Why surfaced:** Title matched the 'instructional_lxd' title family, and the description says "learning content" and "customer education".
- **Overlap:** leads instructional design strategy and customer education for nonprofit software; builds technical curricula and interactive learning; aligns learning content with product releases; measures learner outcomes
- **Stretch:** lead level; owns the move to a custom LMS (SCORM/xAPI/LTI)
- **Caveats:** posted on a recruiter's Ashby board (highlightta), not Neon One's own
- **Worth opening because:** Customer-education ID lead at a company that says it's fully remote.
- **Missing:** salary
- **Seen via:** jobs.ashbyhq.com (recruiter) · **Apply:** https://jobs.ashbyhq.com/highlightta/f36a604d-ac92-4b28-8b5f-54a083fc215e
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### J2. Senior AI Learning Designer, Rapid Content at WRITER
`STRONG OVERLAP · AI CENTRAL` · overlap **strong** · stretch **some** · AI central · salary not stated · posted 2026-09-22
- **Why surfaced:** Title matched the 'ai_learning' and 'instructional_lxd' title families.
- **Overlap:** designs and ships short video courses on software, workflows and AI topics; owns the full course lifecycle; delivers live and virtual training; repurposes content across formats
- **Stretch:** 5+ yrs shipping courses fast; on-camera/voiceover talent for your own teaching
- **Caveats:** text lists office hubs (SF, NYC, Seattle, Austin, Chicago) and never says remote; Jobven tags it remote
- **Worth opening because:** AI-central course building at an enterprise gen-AI company.
- **Missing:** salary, remote policy not explicit in text
- **Seen via:** jobs.ashbyhq.com · **Apply:** https://jobs.ashbyhq.com/writer/263cd86b-f19d-455d-858e-a85acdbe7578
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J3. Senior Scaled Customer Education Specialist at Samsara
`STRONG OVERLAP` · overlap **strong** · stretch **some** · AI present · $80,623 - $121,950 a year · posted 2026-09-03
- **Why surfaced:** Title search for card 7's title, "Customer Education Specialist" (recall probe; outside the 7-day family window).
- **Overlap:** builds and facilitates cohort-based one-to-many customer programs; produces and adapts training materials; builds video tutorials and job aids with AI and authoring tools
- **Stretch:** 3-4 yrs training delivery, 1+ in a scaled model
- **Caveats:** remote in the US **except the SF Bay, NYC and Washington DC metro areas**; check whether your part of MD counts as DC metro. Heavy live facilitation.
- **Worth opening because:** Squarely customer education at a large, stable SaaS company, with a salary band.
- **Seen via:** samsara.com (Greenhouse) · **Apply:** https://www.samsara.com/company/careers/roles/8177646?gh_jid=8177646
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### J4. Sr Product Trainer at Harris Computer (WestCX)
`STRONG OVERLAP` · overlap **strong** · stretch **some** · AI present · salary not stated · posted 2026-09-23
- **Why surfaced:** Description matched: the posting says "learning content" (course_content family).
- **Overlap:** owns internal training strategy for releases; role-based learning paths for Support, Implementations and CS; reusable learning assets and knowledge repositories; AI-assisted content development
- **Stretch:** product depth in public-safety communications software
- **Caveats:** Alabama listed; remote not stated in text (Jobven: remote)
- **Worth opening because:** Curriculum-and-assets training role that isn't titled like one.
- **Missing:** salary, remote policy not explicit in text
- **Seen via:** harriscomputer.wd3.myworkdayjobs.com · **Apply:** https://harriscomputer.wd3.myworkdayjobs.com/en-US/1/job/Alabama-United-States/Sr-Product-Trainer_R0046681-1
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J5. Sales Enablement Specialist at Seven AI
`STRONG OVERLAP · WILDCARD` · overlap **strong** · stretch **some** · AI present · salary not stated · posted 2026-09-22
- **Why surfaced:** Description matched: the posting says "enablement content" (enablement_material family).
- **Overlap:** builds and runs AE/SE onboarding: curricula, role-based learning paths, certifications; maintains the enablement content library; launch readiness
- **Stretch:** 2+ yrs sales/revenue enablement; Salesforce/Gong ramp reporting; "fluent with AI tooling in a build context"
- **Caveats:** sales audience; Boston listed, remote not stated
- **Worth opening because:** Curriculum work for a sales team at an AI security startup.
- **Missing:** salary, remote policy not explicit in text
- **Seen via:** jobs.ashbyhq.com · **Apply:** https://jobs.ashbyhq.com/sevenai/e06133a6-cc41-4755-a9e1-4b6dd2cdd911
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J6. Senior Revenue Enablement Manager at Payscale
`STRONG OVERLAP · BIG STRETCH · WILDCARD` · overlap **strong** · stretch **big** · AI present · salary not stated · posted 2026-09-24
- **Why surfaced:** Description matched: the posting says "curriculum development" and "enablement content".
- **Overlap:** designs learning programs and onboarding: curriculum development, content creation, facilitation; training needs assessments; LMS and knowledge-base stack; AI tools (Claude named)
- **Stretch:** 5-7 yrs enablement/L&D; owns ROI; leads cross-functional teams
- **Caveats:** revenue audience; can't hire in Quebec, Northern Ireland or Hawaii (MD is fine)
- **Worth opening because:** L&D-style design work under an enablement title, remote-first.
- **Missing:** salary
- **Seen via:** jobs.ashbyhq.com · **Apply:** https://jobs.ashbyhq.com/payscale/8300af8d-afb3-422d-a02c-1fec625dfe4d
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### J7. Senior Technical Enablement Program Manager at Wiz
`BIG STRETCH · WILDCARD` · overlap **partial** · stretch **big** · AI present · $136k - $185k a year · posted 2026-09-21
- **Why surfaced:** Description matched: the posting says "knowledge base" (knowledge_content family). This was the only path to it.
- **Overlap:** turns product updates into playbooks, troubleshooting trees, API doc summaries and checklists; leads enablement sessions and builds the decks
- **Stretch:** 5+ yrs technical enablement/TPM in B2B tech; cloud-security depth
- **Caveats:** program-management weighted; remote not stated in text
- **Worth opening because:** Technical content system for a field team, well paid.
- **Missing:** remote policy not explicit in text
- **Seen via:** wiz.io (Greenhouse) · **Apply:** https://www.wiz.io/careers/job/4705217006/:title?gh_jid=4705217006
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J8. Senior Content Designer at Brightspeed
`STRONG OVERLAP · BIG STRETCH` · overlap **strong** · stretch **big** · AI present · salary not stated · posted 2026-09-10
- **Why surfaced:** Title search for "Senior Content Designer" (recall probe).
- **Overlap:** content strategy, frameworks and content models across eCommerce journeys; writes interface and product-education content; sets up AI-assisted content practices
- **Stretch:** 7+ yrs content design / UX writing
- **Caveats:** "prioritize hiring talent in the Charlotte area… hybrid workforce"; Jobven tags it remote; UX writing more than learning
- **Worth opening because:** Content-design systems work with an explicit AI practice angle.
- **Missing:** salary, remote policy not explicit in text
- **Seen via:** jobs.smartrecruiters.com · **Apply:** https://jobs.smartrecruiters.com/Brightspeed/744000148627959-senior-content-designer
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J9. Instructional Designer at Excelsior University
`STRONG OVERLAP` · overlap **strong** · stretch **none** · AI none · $68,000 - $74,000 a year · posted 2026-09-24
- **Why surfaced:** Title search for "Instructional Designer" (recall probe).
- **Overlap:** designs and develops online courses with SMEs and media developers; accessibility and course-design standards
- **Stretch:** 3+ yrs higher-ed online course development
- **Caveats:** Albany NY listed; no remote statement (Jobven: flexible = unclear); higher-ed pay
- **Worth opening because:** Clean ID role at an online-first university.
- **Missing:** remote policy not explicit in text
- **Seen via:** recruiting.ultipro.com · **Apply:** https://recruiting.ultipro.com/EXC1011/JobBoard/eb378fdd-1d75-0520-8078-55ee35061807/OpportunityDetail?opportunityId=59e7fb10-8b66-442a-a687-bb44f2234529
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J10. Senior Manager, Product Enablement at Vultr
`BIG STRETCH · WILDCARD` · overlap **partial** · stretch **big** · AI present · $115k - $130k a year · posted 2026-09-24
- **Why surfaced:** Description matched: the posting says "enablement content" (enablement_material family).
- **Overlap:** recurring product enablement program; turns technical capabilities into training and collateral; certification paths, playbooks, live and on-demand training
- **Stretch:** 5+ yrs product/technical enablement; GPU and cloud infrastructure
- **Caveats:** sales audience; includes competitive battle cards
- **Worth opening because:** Training and certification building for AI infrastructure products; remote stipend stated.
- **Seen via:** jobs.ashbyhq.com · **Apply:** https://jobs.ashbyhq.com/vultr/e03f8f23-d1e7-4788-a9c8-e6a0e47bbad3
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### J11. Learning Management Specialist at Mariner
`` · overlap **partial** · stretch **some** · AI none · salary not stated · posted 2026-09-19
- **Why surfaced:** Description matched: the posting says "learning content" (course_content family).
- **Overlap:** Docebo LMS administration; manages learning content and users; supports org-wide learning initiatives
- **Stretch:** 3 yrs LMS admin, 1+ yr Docebo
- **Caveats:** admin and ops more than content creation; remote not stated in text
- **Worth opening because:** An adjacent L&D-ops role, if LMS work is of interest.
- **Missing:** salary, remote policy not explicit in text
- **Seen via:** jobs.ashbyhq.com · **Apply:** https://jobs.ashbyhq.com/mariner-careers/c157e8fe-1e73-4b27-bd98-400a9ac42546
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J12. Community Web Manager at ServiceNow
`BIG STRETCH · WILDCARD` · overlap **partial** · stretch **big** · AI present · salary not stated · posted 2026-09-22
- **Why surfaced:** Description matched: the posting says "content governance" and "content operations" (knowledge_content family). This was the only path to it.
- **Overlap:** publishing ops and content management for the ServiceNow Community; product hub experiences; content migrations; self-service publishing training and docs
- **Stretch:** 7+ yrs web publishing/CMS; Khoros
- **Caveats:** ServiceNow assigns a "work persona" (remote, flexible or in office) after hire; heavy on web ops
- **Worth opening because:** Content-operations work at a big platform, under a title you wouldn't search for.
- **Missing:** salary, remote policy not explicit in text
- **Seen via:** jobs.smartrecruiters.com · **Apply:** https://jobs.smartrecruiters.com/ServiceNow/744000151110030-community-web-manager
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J13. Senior Content Strategist - Freelance at AKQA
`STRONG OVERLAP · BIG STRETCH` · overlap **strong** · stretch **big** · AI none · $3,000 - $3,400 a week · posted 2026-09-24
- **Why surfaced:** Title matched the 'content_dev' title family; the description also says "content governance".
- **Overlap:** end-to-end content strategy for a flagship financial-services platform: audits, target vision, content frameworks and systems
- **Stretch:** 8+ yrs content strategy for digital products; senior client stakeholders
- **Caveats:** freelance contract; agency (WPP); says "Remote (US Based)" but agency boilerplate mentions required in-office days
- **Worth opening because:** High-rate freelance content-strategy engagement.
- **Seen via:** akqa.com (Greenhouse) · **Apply:** https://www.akqa.com/jobs/8224008/?gh_jid=8224008
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### J14. Marketing Enablement Manager at Blend360
`` · overlap **partial** · stretch **some** · AI present · $60 - $65 an hour · posted 2026-09-21
- **Why surfaced:** Description matched: the posting says "enablement materials" (enablement_material family).
- **Overlap:** sales enablement materials, training resources, and educational content that translates complex offerings
- **Stretch:** 5+ yrs marketing/enablement/PM
- **Caveats:** contract; about half project management; exec decks
- **Worth opening because:** Remote contract content work; "Fully remote within the U.S." is stated.
- **Seen via:** jobs.smartrecruiters.com · **Apply:** https://jobs.smartrecruiters.com/Blend360/744000150785680-marketing-enablement-manager
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### J15. Senior Sales Enablement Manager, SMB & Mid-Market at Fetch
`BIG STRETCH` · overlap **partial** · stretch **big** · AI present · $141,131 - $166,036 a year · posted 2026-09-18
- **Why surfaced:** Description matched: the posting says "enablement content", "playbooks and training" and "onboarding content".
- **Overlap:** role-specific learning paths, training, certifications, playbooks, talk tracks; maintains content in Letter AI
- **Stretch:** 8+ yrs sales enablement/training; SMB/MM sales-motion design
- **Caveats:** sales-methodology heavy
- **Worth opening because:** Learning-path design, well paid, remote anywhere in the US.
- **Seen via:** jobs.gem.com · **Apply:** https://jobs.gem.com/fetch/am9icG9zdDr29lsEVoI2j4k95bL86s-M
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

## 8. Recommendation

**TheirStack only, for now.** Jobven neither replaces it nor earns a place next to it on this evidence.

1. **Recall decides it.** Jobven found 0 of 7 glads and 4 of 35 interesting spike jobs, and most of the missing employers aren't in its company index at all. The decision frame's floor was ~3 of 7.
2. **The net is ~13× smaller.** Equivalent breadth gives ~17 cards and ~2.5 interesting a day, against TheirStack's ~213 and ~45-50.
3. **What Jobven does well doesn't cover that gap.**
   - Every apply link goes to the employer, 55% of postings carry salary, and there's less staffing noise.
   - It saw White Circle 11 days before TheirStack.
   - The scouting pass handles most of the rest anyway: employer links can be pulled from TheirStack's `final_url` or the posting, and the remote check reads the text.
4. **The one thing that could change it is Rone's marks on J1-J15.** If he marks several glad (say 4 or more of 15), check whether TheirStack has those jobs before deciding. That's a title + company lookup, ≤15 of the 22 remaining TheirStack free credits, and it needs his OK.
   - **If TheirStack is missing them:** Jobven at $79/mo alongside it is cheap, and every REST variant fits Starter.
   - **If TheirStack has them:** the value is attention novelty that TheirStack already delivers.
5. **Revisit in 3-6 months.** Jobven's index grew from ~10k postings (Dec 2025) to ~466k active. Re-running `bakeoff/jobven_recall.py` against new glads costs under 100 jobs.

The trial ends around 2026-10-01 with 2,219 jobs unused. Nothing was bought.

## Files

- `bakeoff/jobven_client.py`: logged client. It enforces per-phase caps, always sends `limit`, and saves raw responses.
- `bakeoff/jobven_sem.py`, `bakeoff/jobven_recall.py`, `bakeoff/jobven_family.py`: phases 1-3.
- `bakeoff/jobven_collect.py` → `bakeoff/jobven_jobs.jsonl`: all 190 delivered jobs, flattened.
- `bakeoff/jobven_scouting.py` → `bakeoff/jobven_scouting_analysis.jsonl` + `bakeoff/jobven_metrics.json`: scouting labels and quality metrics.
- `bakeoff/jobven_quality_sample.json`, `bakeoff/jobven_recall.json`, `bakeoff/jobven_family_sizes.json`, `bakeoff/jobven_family_jobs.jsonl`, `bakeoff/jobven_ts_overlap.json`
- `bakeoff/jobven_cards_marks.csv`: mark sheet for J1-J15.
- `bakeoff/raw/jobven_log.jsonl`, `bakeoff/raw/jobven_*.json`, `bakeoff/raw/jobven_docs/`
