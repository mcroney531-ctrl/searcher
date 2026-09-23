# TheirStack Source Spike: Results

Run 2026-09-23 against TheirStack `/v1/jobs/search`, filtered to US, `workplace_types_or: [remote]`, posted in the last 7 days. The spike spent 150 of 200 free credits; 50 are left in reserve. Every raw response is in `bakeoff/raw/`, and per-query credits are in `bakeoff/raw/credit_log.jsonl`. The scouting analysis (`analysis/scouting.yaml` v0.2-draft, run by claude-opus-5-5) covers all 144 sampled jobs and is in `bakeoff/scouting_analysis.jsonl`.

> **Correction after Rone's card review:** the analysis only caught Maryland exclusions when a posting named MD directly. When a posting lists the states it will hire in (for example Springboard: CA/FL/TX/MA/AZ/NY/IL), MD has to be on that list. A re-scan found 2 misses: Springboard (card 1) and Bryan University. Both are now suppressed, and interesting drops from **39 to 37**; the numbers below are the originals. The rule is now in `analysis/scouting.yaml` under `eligibility`.

**Bottom line.** TheirStack works as the retrieval backbone. Title families are dependable, description-pattern search works, and the descriptions are complete. It is not a novelty source: 80% of the sampled jobs came from LinkedIn or Indeed. Rone checks those boards already, so most of TheirStack's value is surfacing titles he wouldn't search for (attention novelty), not jobs he can't reach. The gaps point to direct ATS / careers-page retrieval as the complementary source, with Google Jobs via SerpAPI as a cheap way to check it.

## How the spike ran

- **Free counting doesn't exist.** The docs ("Counting results") say counts cost like any search: 1 credit per returned job, and zero-result queries are free. `blur_company_data` preview mode can't be used for counting and is deprecated for new workspaces. The cheapest sizing call is `limit: 1` + `include_total_results: true`, which costs 1 credit and returns one real sample job.
- **Free-plan limits:** at most 25 results per page, and 10 requests per minute. The credit-balance endpoint is free but counts toward the rate limit.
- **Phases:** 19 sizing calls (1 credit each), then stratified samples. Title families got 7 jobs each, description families 9 each, and the wildcard stratum 35. The wildcard stratum is all description phrases with `job_title_pattern_not` excluding obvious content/learning titles. Samples used `job_id_not` so no job was paid for twice. Samples are the newest postings (`date_posted desc`), mostly posted 2026-09-22 and 2026-09-23.
- **Description search works.** `job_description_pattern_or` takes regex (`(?i)` makes it case-insensitive); `job_description_contains_or` takes whole words. This was the open question in `docs/reframe.md` §1.

| query | 7-day total | credits |
|---|---:|---:|
| title: content_dev | 33 | 1+7 |
| title: instructional_lxd | 46 | 1+7 |
| title: curriculum_training | 20 | 1+7 |
| title: enablement_education (with must-description) | 31 | 1+7 |
| title: technical_content (with AI must-description) | 29 | 1+7 |
| title: ai_learning | 127 | 1+7 |
| desc: course_content | 141 | 1+9 |
| desc: curriculum | 212 | 1+9 |
| desc: enablement_material | 201 | 1+9 |
| desc: customer_training | 273 | 1+9 |
| desc: knowledge_content | 650 | 1+9 |
| desc: ai_adoption | 316 | 1+9 |
| **union of all title families** | **314** | 1 |
| **union of all description families** | **1,695** | 1 |
| title ∩ description | 78 | 1 |
| description, non-obvious title (wildcard pool) | 1,432 | 1+25+10 |
| title union, any workplace (no remote filter) | 1,984 | 1 |
| title union, excluding linkedin.com/indeed.com | 117 | 1 |
| description union, excluding linkedin.com/indeed.com | 676 | 1 |

## 1. What TheirStack surfaces

Real examples from the sample, with the full cards at the end:
- **On-target titles:** Springboard *Content Development Manager*, Veeva *Technical Curriculum Developer – AI Agents*, Fortra *Offensive Security Training Content Developer*, A.T. Still University *Instructional Designer (remote)*, Commerce (BigCommerce) *Technical Training Content Developer*.
- **Description-only finds with titles you wouldn't search:**
  - BCBS North Carolina *Senior Digital Product Analyst*: the work is an enterprise content-governance model plus regulated content development.
  - Save the Children *Senior Lead, AI, Digital and Data Capacity Development*: the work is AI training and literacy rollout.
  - ZipLiens *Director of Onboarding & Enablement*: builds a knowledge base, tutorial videos and an enablement curriculum.
  - NICE *Senior Education Professional*: ILT, vILT and eLearning content development.
- **Noise:** field-sales territories, clinical and nursing educators, IT help desks, $17/hr call-center roles, ML engineers matched by "AI" title words, and internships.

## 2. Title families vs description families

The rows below are the remote-filtered sample, n=143. The one any-workplace sizing job is excluded. "Interesting" means overlap is strong or partial and the job isn't suppressed.

| | title families | description families | wildcard pool (description + non-obvious title) |
|---|---:|---:|---:|
| 7-day volume (remote, US) | 314 (~45/day) | 1,695 (~242/day) | 1,432 (~205/day) |
| sampled | 48 | 60 | 35 |
| strong / partial / weak / very_low | 20 / 14 / 5 / 9 | 3 / 5 / 10 / 42 | 1 / 1 / 4 / 29 |
| **interesting** | **30 (62%)** | **7 (12%)** | **2 (6%)** |
| interesting wildcards | 0 | 3 | 2 |
| client-facing (owns accounts) | 1 | 22 | 7 |

Per family:
- **Title families:** instructional_lxd had 8 of 8 interesting and curriculum_training 5 of 7 (the 2 misses were HCA's Maryland exclusion). enablement_education had 6 of 8; its "academy" term pulls in schools and tutoring. content_dev had 5 of 8. technical_content had 3 of 8; it picks up AI-evaluation gigs. **ai_learning had 2 of 8** and is the noisiest title family: "AI enablement" and "AI learning" match ML-engineer and finance-automation titles.
- **Description families:** course_content had 4 of 10 interesting and curriculum 3 of 10. **customer_training, enablement_material, knowledge_content and ai_adoption had 0 of 40.** These phrases mostly retrieve sales, customer success and support jobs. "knowledge base" alone is 650/week of mostly help-desk work.
- **But the best wildcards came from those same families.** Save the Children matched "AI adoption" and BCBS NC matched "content governance". So tighten the phrases (keep "content governance", "AI literacy", "AI training program"; drop bare "knowledge base", "customer training", "customer education" and "AI adoption"), size each phrase separately (1 credit each), and add `job_title_not` for sales and support titles. Don't delete the families.

Verdict: title families give volume at about 60% relevance. Description families as written are about 88% noise, but they're the only place the unexpected titles came from.

## 3. Interesting and wildcard yield

- **39 of 143** remote-filtered jobs are interesting: 30 from title families, 7 from description families and 2 from the wildcard pool.
- **5 interesting wildcards:** Khan Academy (fundraising copywriting contract), ZipLiens, Medtronic field-service curriculum, Save the Children and BCBS NC. A sixth, Bechtel's AI-enablement training role, is a strong wildcard but was suppressed as hybrid.
- **6 of the 39** interesting jobs have AI as central. 19 of 143 jobs overall mention AI centrally, but most of those are engineering roles.
- The scale projection is in §7.

## 4. Duplication and noise

- **Duplicates:** 8 of 144 rows (5.6%) repeat another job's description under a different ID. Company-name dedupe would not have caught all of them:
  - Moen/Fortune Brands CSR ×4 (one per city)
  - Smartcat Director of Sales ×3 ("Smartcat" and "smARTcat")
  - HCA Training Developer ×2 (one under company **"Work From Home"**)
  - MLabs ×2, TalentHop ×2
  - Dedupe needs a description hash plus normalized company, not `(company, title)`. `schema/jobs.sql`'s `job_dedupe` index is not enough.
- **Cross-query overlap:** 78 of the 314 title-family jobs (25%) also match a description family. The description families overlap each other by about 6% (they sum to 1,793 against a union of 1,695).
- **Staffing and aggregator relistings:** 27 of 144 (19%) come from TalentHop, Jobgether, Ladders and similar sites that post "our client" jobs, so the employer is hidden. They inflate volume and hide the employer's real posting.
- **The remote flag is unreliable.** All 143 were flagged `remote: true`, but the posting text reads:

  | text says | jobs | share |
  |---|---:|---:|
  | remote | 69 | 48% |
  | unclear | 40 | 28% |
  | field territory with 20-85% travel | 20 | 14% |
  | onsite | 13 | 9% |
  | hybrid | 1 | 1% |

  Examples: "Onsite – Sawtelle", a cleared TS/SCI role in DC, and Bechtel "Part-Time Telework". Treat TheirStack's flag as retrieval recall only; the scouting pass has to re-check it.
- **Maryland exclusion:** there's no structured field for it. The HCA posting ("must live within 60 miles of an HCA hospital" in 14 listed states, not MD) was caught only by reading the text. Only 1 distinct job in the sample did this, but it's invisible to filters. The analyzer has to check for it, and the posting stays suppressed but browsable.
- **Suppressed under your declared constraints:** 16 of 143 (location impossible: onsite, hybrid or MD excluded).

## 5. Source novelty (off LinkedIn/Indeed)

- **Sample:** `source_url` was LinkedIn for 79 jobs and Indeed for 36, which is **115 of 144 (80%) on the major boards**. 29 (20%) came from ATS pages: Workday 7, SmartRecruiters 5, Ashby 4, Workable 3, Greenhouse 2, and others. Among interesting jobs, 6 of 39 (15%) were off-board.
- **7-day counts with `url_domain_not: [linkedin.com, indeed.com]`:** 117 of 314 title jobs (**37%**) and 676 of 1,695 description jobs (**40%**) were seen only off the boards. The sample was newest-first, and the freshest day skews toward LinkedIn scrapes. That suggests ATS scraping lags a day or more, which is worth checking because freshness matters.
- **Read both numbers as upper bounds.** TheirStack records one source per job, so a job scraped from Workday can still be on LinkedIn. Source novelty is somewhere between 15% and 40%, and verifying it needs a cross-check against LinkedIn or Google Jobs.
- **Implication:** TheirStack largely re-serves LinkedIn and Indeed. Its value to Rone is mainly *attention novelty* (BCBS NC's analyst title is on LinkedIn, but he'd never search for it) plus a minority of truly off-board ATS postings.

## 6. Description completeness and apply URLs

- **Descriptions are full, not snippets.** Across 144 jobs the minimum was 1,552 chars, the median 5,944 and p90 10,059; none were under 1,000. One posting was mostly boilerplate. That's enough to run scouting notes without re-fetching, as the design requires.
- **A real employer/ATS apply URL (`final_url`)** is present for **59 of 144 (41%)**. That includes 23 of the 115 LinkedIn/Indeed-sourced jobs, for example Springboard seen via Indeed with a Greenhouse apply link. **85 of 144 (59%)** have only a LinkedIn or Indeed link; 25 are LinkedIn Easy Apply.
- **Salary** is present for 39 of 144 (27%). **Employment type** is missing for 16. Several structured fields are wrong: a $50k "director" salary, a construction role tagged as an internship, a professor tagged "volunteer" under company "Women In Science". Treat structured fields as hints.

## 7. Projected volume and cost at full wide-net scale

**Volume.** The 7-day counts were divided by 7. Daily incremental pulls should filter on `discovered_at_gte` (plus `job_id_not` as a guard) so no job is billed twice.

| configuration | jobs/day | credits/month | expected interesting/day |
|---|---:|---:|---:|
| as written (all families) | ~276 | ~8,300 | ~50 (28 title + 22 description) |
| title families + course_content and curriculum + tightened narrow phrases (estimate) | ~100-120 | ~3,000-3,600 | ~40-45 |

The as-written config shows 276 cards a day against your 100-card review budget, with about 80% weak or very_low. It still works under amendment 5 (the review budget isn't a discovery cap) because ordering puts the ~50 interesting cards first. The tightened set roughly fits the budget with little lost; the tightened numbers are an estimate until each phrase is sized.

**TheirStack plans** (theirstack.com/en/pricing, monthly; unused credits roll over 12 months):

| plan | price | fits |
|---|---:|---|
| 1,500 credits | $49 | neither configuration |
| 5,000 credits | $100 | tightened (~3,000-3,600/month) |
| 10,000 credits | $169 | as written (~8,300/month) |
| 20,000 credits | $240 | as written with room to widen |

**Analysis cost** (one scouting note per job). Assumes about 2.5k input tokens (a median description of about 1.5k tokens plus the rubric) and about 600 output tokens including thinking. Prices are Anthropic list prices per MTok, input/output.

| model | $/job | as written, 8.3k/month | tightened, 3.3k/month | with Batch API (−50%) |
|---|---:|---:|---:|---:|
| Claude Haiku 4.5 ($1/$5) | $0.0055 | $46 | $18 | $23 / $9 |
| Claude Sonnet 5 ($2/$10) | $0.011 | $91 | $36 | $46 / $18 |
| Claude Opus 5 ($5/$25) | $0.028 | $228 | $91 | $114 / $46 |

**Total monthly cost:**
- As written: $169 TheirStack + $23-228 analysis.
- Tightened: $100 TheirStack + $9-91 analysis.

The notes in this spike were hand-run at Opus-class quality. `bakeoff/scouting_analysis.jsonl` can serve as the reference labels for checking whether a cheaper model's tags agree before choosing one.

## 8. Is TheirStack enough as the primary source?

**It's enough as the primary backbone but not as the only source.** The gaps and what each one points to:

1. **Source novelty is capped (15-40%)** because TheirStack mostly re-serves LinkedIn and Indeed. → **Complement: direct ATS / careers-page retrieval.** This means Greenhouse, Lever and Ashby public job-board APIs, plus Workday, for a growing watchlist of companies. Every off-board hit and every `final_url` in TheirStack reveals another `(ats_kind, ats_slug)` for `company.ats_slug`. Much of the needed discovery already exists.
2. **59% of jobs lack an employer apply URL.** ATS-direct retrieval supplies that URL by construction.
3. **The remote flag and state eligibility are unreliable.** No source fixes this; the analyzer has to read the text.
4. **Cheap check before building ATS-direct:** Google Jobs via SerpAPI (250 free searches are available, and the key is verified). Each result lists every place a posting appears ("apply on LinkedIn / Indeed / company site"). Running it against the 39 interesting jobs here would measure true on-board status and show whether Google Jobs finds careers-page postings TheirStack missed.

## Files

- `bakeoff/theirstack_spike.py`: the spike runner (size / sample / offboard phases); logs credits and saves raw responses.
- `bakeoff/raw/*.json`, `bakeoff/raw/credit_log.jsonl`: every raw response and the per-call credit log.
- `bakeoff/jobs_sample.jsonl`: 144 flattened jobs. `bakeoff/spike_stats.py` rebuilds this file and the stats.
- `bakeoff/scouting_rows.py` → `bakeoff/build_scouting.py` → `bakeoff/scouting_analysis.jsonl` + `bakeoff/spike_metrics.json`: the full scouting output for all 144 jobs.
- `bakeoff/spike_cards.md`, `bakeoff/spike_cards_marks.csv`: the 20 cards below, and a sheet for your marks.

## Sample cards: mark "glad I saw this"

These are 20 cards. The first 19 are chosen for range: on-target titles, wildcards, off-board postings and AI-central roles. Card 20 is a filtered job, included so you can check the suppression rule. Marks go in `bakeoff/spike_cards_marks.csv`, or reply with card numbers.

### 1. Content Development Manager at Springboard
`STRONG OVERLAP · BIG STRETCH` · overlap **strong** · stretch **big** · AI present · salary not stated · posted 2026-09-23
- **Why surfaced:** Title matched a title-family sizing query: "Content Development Manager".
- **Overlap:** owns end-to-end instructional content creation; builds new courses end to end incl. AI/tech courses; works with SMEs/instructors
- **Stretch:** 8-10 yrs learning design/content development
- **Caveats:** California listed; remote not stated in excerpt
- **Worth opening because:** Near-perfect title and duties at Springboard; the years ask is the stretch.
- **Missing:** salary, remote policy not explicit in text, employment type
- **Seen via:** indeed.com · **Apply:** https://job-boards.greenhouse.io/springboardmentors/jobs/6099256004?gh_src=a8f5a1e84us
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 2. Director of Onboarding & Enablement (Remote) at ZipLiens
`STRONG OVERLAP · BIG STRETCH · WILDCARD · OFF MAJOR BOARDS` · overlap **strong** · stretch **big** · AI none · salary not stated · posted 2026-09-23
- **Why surfaced:** Description matched: the posting says "training curriculum" (curriculum family).
- **Overlap:** builds customer enablement library: knowledge base, tutorial videos, one-pagers, training decks; builds internal enablement curriculum; content governance model
- **Stretch:** Director; 5+ yrs onboarding/education; 3+ yrs owning a program; hiring
- **Caveats:** travel up to 20%; also runs onboarding operations; legal-services niche
- **Worth opening because:** Build-the-content-system-from-scratch role, off the major boards (Workable).
- **Missing:** salary
- **Seen via:** jobs.workable.com · **Apply:** https://jobs.workable.com/view/fbMvLYNdbxBJzMDUsuUrXZ/director-of-onboarding-&-enablement-(remote)-in-somerset-at-zipliens
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 3. Senior Education Professional, Development at NICE
`STRONG OVERLAP` · overlap **strong** · stretch **some** · AI none · salary not stated · posted 2026-09-23
- **Why surfaced:** Description matched: the posting says "Learning content" (course_content family).
- **Overlap:** designs ILT, vILT and eLearning content; owns needs analysis, curriculum design, content development; writes lab guides and technical docs
- **Stretch:** maintains training lab servers/databases
- **Caveats:** technical product (contact-center analytics); listed Atlanta; 'telecommuting permitted'
- **Worth opening because:** Core content-development job for a software product.
- **Missing:** salary, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4468944650/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 4. Technical Curriculum Developer - AI Agents - Remote at Veeva Systems
`STRONG OVERLAP · BIG STRETCH · AI CENTRAL` · overlap **strong** · stretch **big** · AI central · salary not stated · posted 2026-09-22
- **Why surfaced:** Title matched the 'curriculum_training' title family: "Technical Curriculum Developer - AI Agents - Remote".
- **Overlap:** builds training for customers/partners on agentic AI; technical curriculum development; builds demo agents
- **Stretch:** demonstrable AI-agent building; API tooling (Git/Postman); 3+ yrs technical training
- **Caveats:** says 'do not apply if you have dabbled with AI agents'
- **Worth opening because:** AI-central curriculum role at Veeva; stretch is hands-on agent building.
- **Missing:** salary, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4452423591/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 5. Senior Digital Product Analyst at Blue Cross and Blue Shield of North Carolina
`STRONG OVERLAP · WILDCARD` · overlap **strong** · stretch **some** · AI present · $98,092 - $156,947 a year · posted 2026-09-23
- **Why surfaced:** Description-only find (title not an obvious content/learning title): the posting says "content governance" (knowledge_content family).
- **Overlap:** leads enterprise content governance model and taxonomy; leads content development for regulated segments; AI engine optimization of content
- **Stretch:** 5+ yrs; regulated health-insurance content
- **Caveats:** title says 'Digital Product Analyst'; NC listed; remote unclear
- **Worth opening because:** Content-governance work hiding under an analyst title; a real wildcard.
- **Missing:** remote policy not explicit in text
- **Seen via:** indeed.com · **Apply:** https://bcbsnc.wd5.myworkdayjobs.com/en-US/BCBSNC/job/Remote-Flex---North-Carolina/Senior-Digital-Product-Analyst_RQ0019407
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 6. Senior Lead, AI, Digital and Data Capacity Development at Save the Children
`BIG STRETCH · WILDCARD · AI CENTRAL` · overlap **partial** · stretch **big** · AI central · salary not stated · posted 2026-09-23
- **Why surfaced:** Description-only find (title not an obvious content/learning title): the posting says "AI adoption" (ai_adoption family).
- **Overlap:** oversees development and rollout of AI training and culture-change initiatives; builds staff capacity to use data and AI
- **Stretch:** senior leadership across a global NGO; chairs exec forums; dotted-line management
- **Caveats:** international travel up to 20%; strategy/leadership heavier than content; closes 7 Oct 2026
- **Worth opening because:** AI-literacy capacity building at Save the Children; found on their own careers site.
- **Missing:** salary
- **Seen via:** indeed.com · **Apply:** https://www.savethechildren.net/careers/apply/details?jid=17764
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 7. Customer Education Specialist at Citian
`STRONG OVERLAP` · overlap **strong** · stretch **some** · AI none · salary not stated · posted 2026-09-23
- **Why surfaced:** Title matched the 'enablement_education' title family: "Customer Education Specialist".
- **Overlap:** builds first customer training program from scratch; learner personas; foundational curriculum and how-to content
- **Stretch:** LMS selection/config
- **Caveats:** contract; DC office preferred, remote open
- **Worth opening because:** Build-it-from-zero customer education; good portfolio role.
- **Missing:** salary, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4469498053/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 8. Training Developer at Edgewater Technical Associates
`STRONG OVERLAP` · overlap **strong** · stretch **some** · AI none · salary not stated · posted 2026-09-22
- **Why surfaced:** Title matched the 'curriculum_training' title family: "Training Developer".
- **Overlap:** designs curricula, learning paths, participant guides, assessments, job aids; ILT, virtual and e-learning; job task analysis
- **Stretch:** oil & gas / safety domain
- **Caveats:** contract Oct 2026-Mar 2027 via staffing firm; technical/safety/compliance content
- **Worth opening because:** Textbook training-development contract; remote; apply link on Loxo, not the boards.
- **Missing:** salary, employment type
- **Seen via:** indeed.com · **Apply:** https://edgewater-technical-associates.app.loxo.co/job/Mjg2ODEtdGQ1NWtqajFxYjJleDJyeA==?source_type=indeed&t=1790104067
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 9. Offensive Security Training Content Developer at Fortra
`STRONG OVERLAP · BIG STRETCH · OFF MAJOR BOARDS` · overlap **strong** · stretch **big** · AI none · $115k - $140k per year · posted 2026-09-23
- **Why surfaced:** Title matched the 'content_dev' title family: "Offensive Security Training Content Developer".
- **Overlap:** designs courses, modules, hands-on labs, assessments, certifications, learning paths
- **Stretch:** deep offensive-security tradecraft (Red Team, Cobalt Strike)
- **Caveats:** security domain expertise required
- **Worth opening because:** Pure course development; domain is the big stretch. $115-140k.
- **Seen via:** fortra.wd12.myworkdayjobs.com · **Apply:** https://fortra.wd12.myworkdayjobs.com/FortraCareers/job/United-States/Offensive-Security-Training-Content-Developer_R26-0288
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 10. Senior Program Manager- AI Learning Operations at Accenture
`AI CENTRAL` · overlap **partial** · stretch **some** · AI central · salary not stated · posted 2026-09-23
- **Why surfaced:** Title matched the 'ai_learning' title family: "Senior Program Manager- AI Learning Operations".
- **Overlap:** coordinates content, video and architecture pods shipping AI courses; runs release readiness for learning programs; sits inside Udacity's learning-experience org
- **Stretch:** 4+ yrs program management; people lead of one PM
- **Caveats:** program management rather than hands-on content; NY listed; MD pay band listed so MD looks eligible
- **Worth opening because:** Udacity (Accenture) AI-course production ops; adjacent-to-core with strong AI angle.
- **Missing:** salary, remote policy not explicit in text, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4469403805/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 11. AI SDLC Enablement Consultant at Crew
`AI CENTRAL` · overlap **partial** · stretch **some** · AI central · salary not stated · posted 2026-09-23
- **Why surfaced:** Title matched the 'ai_learning' title family: "AI SDLC Enablement Consultant".
- **Overlap:** develops playbooks, training materials, success metrics for AI tool adoption; runs workshops upskilling teams
- **Stretch:** 2+ yrs hands-on scaling AI tools in SDLC
- **Caveats:** consulting firm; client assignments; engineering audience (Copilot, Jira AI)
- **Worth opening because:** AI-adoption enablement content, 100% remote.
- **Missing:** salary, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4470665790/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 12. Technical Training Content Developer at Commerce
`STRONG OVERLAP` · overlap **strong** · stretch **some** · AI present · salary not stated · posted 2026-09-19
- **Why surfaced:** Title matched the 'technical_content' title family: "Technical Training Content Developer".
- **Overlap:** creates product training and technical learning content; scripts/narrates video; uses AI tools for content creation
- **Stretch:** 3-5 yrs tech + developer audience
- **Caveats:** Texas listed; remote unclear
- **Worth opening because:** Core technical training content role at BigCommerce parent.
- **Missing:** salary, remote policy not explicit in text, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4441657942/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 13. Customer Success Content & Enablement Manager at Arrow Electronics
`STRONG OVERLAP` · overlap **strong** · stretch **some** · AI none · salary not stated · posted 2026-09-23
- **Why surfaced:** Title matched the 'enablement_education' title family: "Customer Success Content & Enablement Manager".
- **Overlap:** owns customer-success content ecosystem; sales enablement training; customer stories library
- **Stretch:** 3-5 yrs content + PM
- **Caveats:** Centennial CO listed; must travel to Arrow office on request
- **Worth opening because:** Content + enablement ownership; check remote status.
- **Missing:** salary, remote policy not explicit in text, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4453071056/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence medium

### 14. CGHS - Instructional Designer (remote) at A T Still University Of Health Sciences
`STRONG OVERLAP` · overlap **strong** · stretch **none** · AI none · salary not stated · posted 2026-09-22
- **Why surfaced:** Title matched the 'instructional_lxd' title family: "CGHS - Instructional Designer (remote)".
- **Overlap:** partners with faculty to design online courses; UDL/accessibility; Canvas
- **Caveats:** higher-ed pay likely
- **Worth opening because:** Clean remote higher-ed instructional designer role.
- **Missing:** salary
- **Seen via:** indeed.com · **Apply:** https://recruiting.paylocity.com/Recruiting/Jobs/Details/4517702/ATSU-PUBLIC/CGHS-Instructional-Designer-remote?source=Indeed_Feed
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 15. Business Development Course Developer at Shipley Associates
`STRONG OVERLAP · BIG STRETCH` · overlap **strong** · stretch **big** · AI present · $60,000 - $75,000 a year · posted 2026-09-22
- **Why surfaced:** Description matched: the posting says "course development" (course_content family).
- **Overlap:** instructional design and curriculum development; course modernization; AI-enabled content development tools
- **Stretch:** 5+ yrs instructional design; 3+ yrs government BD/capture experience
- **Caveats:** part-time; $60-75k; government-contracting BD domain required
- **Worth opening because:** Content development plus AI tooling; domain ask is the stretch.
- **Missing:** employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** indeed.com · **Apply:** http://www.indeed.com/job/business-development-course-developer-92fd1e3e60c4be8b
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 16. Interim Associate Manager, Email Marketing (3-month contract, $42/hour, 20 hours/week) at Khan Academy
`WILDCARD · OFF MAJOR BOARDS` · overlap **partial** · stretch **some** · AI present · salary not stated · posted 2026-09-23
- **Why surfaced:** Description matched: the posting says "learning content" (course_content family).
- **Overlap:** writes and edits all fundraising email copy in multiple brand voices; uses AI tools to streamline copy-editing
- **Stretch:** Salesforce Marketing Cloud production
- **Caveats:** 3-month contract to 1/4/2027; 20 hrs/week at $42/hr; fundraising, not learning
- **Worth opening because:** Short, remote writing gig at Khan Academy; a stopgap or portfolio piece, found on Greenhouse.
- **Missing:** salary, employment type
- **Seen via:** job-boards.greenhouse.io · **Apply:** https://job-boards.greenhouse.io/khanacademy/jobs/8226809
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 17. Sr Manager of Curriculum and Instruction (Remote) at Ladders
`STRONG OVERLAP · BIG STRETCH` · overlap **strong** · stretch **big** · AI none · salary not stated · posted 2026-09-21
- **Why surfaced:** Title matched the 'curriculum_training' title family: "Sr Manager of Curriculum and Instruction (Remote)".
- **Overlap:** leads curriculum materials and instructional programs; instructional standards and accessibility
- **Stretch:** 7+ yrs curriculum/instructional leadership; manages team
- **Caveats:** client unnamed (Ladders listing); licensure-aligned content
- **Worth opening because:** Senior curriculum leadership, remote, $102-132k.
- **Missing:** salary, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4467372895/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 18. Technical Content Writer (Contract) at AfterQuery
`AI CENTRAL · OFF MAJOR BOARDS` · overlap **partial** · stretch **some** · AI central · $124.8k per year · posted 2026-09-21
- **Why surfaced:** Title matched the 'technical_content' title family: "Technical Content Writer (Contract)".
- **Overlap:** public-facing technical writing about AI data work
- **Stretch:** technical AI audience
- **Caveats:** 10-15 hrs/week, $60/hr, 6-month contract
- **Worth opening because:** Part-time AI content writing (Ashby, off-board).
- **Seen via:** jobs.ashbyhq.com · **Apply:** https://jobs.ashbyhq.com/afterquery/6f90701a-f9b5-4599-a288-470fcd200640
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 19. Content Lead at White Circle
`AI CENTRAL` · overlap **partial** · stretch **some** · AI central · salary not stated · posted 2026-09-22
- **Why surfaced:** Title matched the 'content_dev' title family: "Content Lead".
- **Overlap:** explainer content on AI safety, evaluation, governance; case studies and reference materials; content process
- **Stretch:** exceptional long-form technical writing
- **Caveats:** marketing/thought-leadership content; LA listed; remote unclear
- **Worth opening because:** AI-central content lead at a small AI-safety company.
- **Missing:** salary, remote policy not explicit in text, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4470619089/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

### 20. Training Developer at HCA Healthcare (FILTERED: state list for remote eligibility excludes Maryland)
`STRONG OVERLAP` · overlap **strong** · stretch **none** · AI none · salary not stated · posted 2026-09-22
- **Why surfaced:** Title matched the 'curriculum_training' title family: "Training Developer".
- **Overlap:** develops, maintains and delivers curricula and course content
- **Caveats:** must live near an HCA hospital; Maryland not in the state list
- **Worth opening because:** Exactly the work, but Maryland is excluded.
- **Missing:** salary, employer apply URL (only a LinkedIn/Indeed link)
- **Seen via:** linkedin.com · **Apply:** https://www.linkedin.com/jobs/view/4470233825/
- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence high

