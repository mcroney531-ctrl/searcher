# Credit Projection: Before Buying a TheirStack Plan

Sizing-only pass run 2026-09-24. Every call used `limit: 1` + `include_total_results: true` with the spike's filters: US, `workplace_types_or: [remote]`, `posted_at_max_age_days: 7`. It made 29 calls and spent 28 credits (one zero-result query was free), leaving **22**. All calls are logged in `bakeoff/raw/credit_log.jsonl` (lines 34-62) with raw responses in `bakeoff/raw/proj_*.json`. The free local checks against the spike's 144 jobs are in `bakeoff/projection_local.py` → `bakeoff/projection_local.json`.

**Recommendation up front:** buy the **10k-credit plan ($169/mo)** and run **Config B** below:
- all 22 description phrases, bare "knowledge base" included
- the 11 title exclusions, on the description pull only

That's about 213 jobs/day and about 6,400 credits/month. It keeps all 7 glads and every interesting spike job. The smaller configurations that fit the 10k plan cost the same, so they buy no savings.

## Same-day baselines

The rolling 7-day window moves. Today's counts are about 10% below the spike day's (2026-09-23), so plan sizes below assume ±10% variance.

| query | 2026-09-23 (spike) | 2026-09-24 |
|---|---:|---:|
| union of all title families | 314 | **276** |
| union of all description phrases | 1,695 | **1,569** |
| title ∩ description (credit log line 15) | 78 | not re-tested (settled) |

## 1. Per-phrase weekly volume

Each phrase was sized alone and in the order you gave, with the likely-junk phrases first. The "sample" columns re-match all 144 stored spike descriptions against each phrase locally.
- **glads:** card numbers of your glads this phrase matches.
- **interesting:** sampled jobs with strong or partial overlap that weren't suppressed.
- **only path:** interesting jobs this phrase reaches that no title family and no other phrase reaches.

Weekly counts overlap, so the column sums to 1,710 against a union of 1,569.

| # | phrase | family | jobs/week | sample matches | glads | interesting | only path |
|---:|---|---|---:|---:|---|---:|---|
| 1 | knowledge base (bare) | knowledge_content | **510** | 38 | — | 3 | — |
| 2 | customer training | customer_training | 180 | 14 | #7 | 2 | — |
| 3 | customer education | customer_training | 84 | 7 | #7 | 6 | — |
| 4 | AI adoption | ai_adoption | 252 | 11 | — | 1 | — (Save the Children also matches #21) |
| 5 | onboarding content | customer_training | 5 | 0 | — | 0 | — |
| 6 | playbooks and training | enablement_material | 3 | 1 | — | 0 | — |
| 7 | develop(ing) course content | course_content | 1 | 0 | — | 0 | — |
| 8 | course development | course_content | 38 | 7 | #14, #15 | 4 | — (Shipley #15 also via #11) |
| 9 | learning content | course_content | 93 | 14 | #12, #17 | 7 | Khan Academy, Solera, NICE |
| 10 | e-learning content | course_content | 10 | 1 | — | 0 | — |
| 11 | curriculum development | curriculum | 116 | 9 | #15, #17 | 6 | — (Shipley #15 also via #8) |
| 12 | design(ing) (the) curriculum | curriculum | 5 | 1 | — | 1 | Univ. of Pittsburgh |
| 13 | training curriculum | curriculum | 75 | 7 | — | 2 | Medtronic field-service training |
| 14 | enablement materials | enablement_material | 143 | 10 | — | 0 | — |
| 15 | enablement content | enablement_material | 65 | 5 | — | 2 | — |
| 16 | academy content | customer_training | 2 | 0 | — | 0 | — |
| 17 | help center content | knowledge_content | 13 | 1 | — | 1 | — |
| 18 | content operations | knowledge_content | 40 | 0 | — | 0 | — |
| 19 | content governance | knowledge_content | 31 | 2 | **#5** | 2 | **BCBS NC (glad #5)** |
| 20 | AI literacy | ai_adoption | 43 | 6 | — | 0 | — |
| 21 | AI training program | ai_adoption | 1 | 1 | — | 1 | — (Save the Children also matches #4) |
| 22 | teach teams to use AI | ai_adoption | 0 | 0 | — | 0 | — |
| | narrowed knowledge base (see below) | knowledge_content | 183 | 13 | — | 1 | — |

What this shows:
- **The two description-found glads rest on low-volume phrases:** "content governance" (31/week) for #5, and "course development" / "curriculum development" (38 and 116/week) for #15. None of the high-volume phrases (knowledge base, AI adoption, customer training, enablement materials) reached a glad or an only-path find in the sample. The sample is small, though: 11-38 matches per phrase. By the brief's rule, that's not grounds to drop them.
- **Five phrases are nearly dead:** onboarding content (5), playbooks and training (3), develop course content (1), academy content (2), AI training program (1), plus teach teams to use AI (0). They cost almost nothing, so keep them. Their narrow wording limits their wildcard value, and looser variants ("AI training", "onboarding materials") are worth sizing later.
- **Narrowed knowledge base:** the pattern is `knowledge[- ]base (articles?|content)` or a verb (writes, builds, creates, develops, maintains, owns, curates) before the knowledge base. It cuts the phrase from 510 to 183/week. In the sample it kept ZipLiens and lost only jobs a title family already reaches (SEO Content Strategist, Spectrio Director of Customer Education).

## 2. Title exclusions for the description pull

The filter is `job_title_pattern_not` (regex), **not `job_title_not`**. The API spec says `job_title_not` is bag-of-words: a pattern excludes any title containing all of its words in any order. So `customer success manager` would also exclude card 13, "Customer Success Content & Enablement Manager". Every term below needs its words adjacent. None uses a bare "Specialist", "Associate", "Analyst" or "Manager"; each is anchored to a sales or support noun. The terms live in `bakeoff/theirstack_spike.py` (`TITLE_EXCLUDE`).

| term | regex (case-insensitive) | why it's safe | risk |
|---|---|---|---|
| account_exec | `\baccount executive` | Quota-carrying sales title with no content variant | low |
| account_manager | `\b(key \|partner \|strategic \|enterprise \|technical )?account manager` | Owns renewals and revenue; content work is never titled this way | low |
| sales_rep | `\bsales (representative\|rep\|executive\|associate\|consultant\|specialist)\b` | "sales" must sit directly before the role noun, so "Sales Enablement Specialist" is kept | low |
| sales_mgmt | `sales (manager\|director)`, `director of sales`, `VP of sales`, `head of sales` | Sales leadership; "Sales Enablement Manager" is kept (tested) | low |
| sales_dev | `sales development`, `SDR`/`BDR`, `business development (representative\|rep\|executive\|manager)` | Prospecting roles; "Business Development Course Developer" (glad #15) is kept (tested) | low |
| territory | `\bterritory (manager\|representative\|sales)\b` | Field-sales territories were a named spike noise class | low |
| presales_eng | `(solutions?\|sales) engineer`, `pre-sales`, `solutions consultant` | Technical pre-sales | **medium:** "Solutions Consultant" sometimes covers demo and enablement content |
| cust_service | `\bcustomer (service\|support\|care) (representative\|rep\|agent\|associate\|advocate\|specialist)\b` | Queue-based support; "Customer Service Training Specialist" is kept (tested) | **medium:** includes "specialist", so a title like "Customer Support Specialist, Knowledge Base" would be dropped |
| tech_support | `\b(technical\|tech\|IT\|application\|desktop) support (specialist\|analyst\|technician\|representative\|rep\|engineer)\b` | Ticket-resolution roles; "Technical Support Content Writer" is kept (tested) | **medium:** same "specialist"/"analyst" caveat as above |
| help_desk | `help desk`, `service desk`, `tier 1/2/3 support`, `call center agent/representative` | Help-desk titles, unambiguous | low |
| cust_success | `\b(customer\|client) success (manager\|associate\|representative\|executive)\b` | Account-ownership roles; "Customer Success Content & Enablement Manager" (card 13) is kept (tested) | **medium:** edtech CSMs sometimes build training. Amendment 2 treats client ownership as a caveat, not a gate, so this is the term most worth watching |

**Deliberately not excluded:** "implementation specialist/manager", "customer advocate", "onboarding specialist", "enablement", "trainer", and any bare "Specialist", "Associate" or "Analyst" (glad #5 is titled "Senior Digital Product Analyst"). Implementation roles often include customer training content.

**Check against the spike's 144 jobs:**
- **The list removes 35 jobs (30 very_low, 5 weak), including 0 of the 7 glads (5, 7, 10, 12, 14, 15, 17) and 0 other interesting jobs.** No loosening was needed.
- Removals by term: cust_service 8, tech_support 8, sales_mgmt 4, cust_success 4, account_manager 3, sales_rep 3, presales_eng 3, help_desk 2.
- Probe titles that stayed in: Customer Success Content & Enablement Manager, Sales Enablement Content Manager, Sales Enablement Manager, Customer Education Specialist, Senior Digital Product Analyst, Business Development Course Developer, Technical Support Content Writer, Customer Service Training Specialist, Account Management Training Lead.

## 3. Volume removed by the exclusions

| query | without exclusions | with exclusions | removed |
|---|---:|---:|---:|
| all 22 description phrases | 1,569 | 1,283 | **286/week (18%), ~41 cards/day** |
| bare "knowledge base" alone | 510 | 380 | 130/week (25%) |

The exclusions apply to Pull B (the description pull) only. Title-family results are never filtered by them.

## 4. Candidate configurations

- Every configuration uses Pull A = all title families (276/week).
- Pull B's volume ≈ description total minus its overlap with Pull A. The overlap was 78 of 1,695 on the spike day, scaled here to about 50-70 per configuration; that estimate is worth ±20 jobs/week, which doesn't change any plan choice.
- Credits/month = jobs/week ÷ 7 × 30.
- Plans are monthly and unused credits roll over 12 months: 5k = $100, 10k = $169, 20k = $240.
- Analysis cost uses the spike's per-job estimate (2.5k in / 600 out tokens) at standard rates with no batching, because batching adds up to 24 hours of delay.

| | **A: as written** | **B: + title exclusions** | **C: B + narrowed KB** | **D: 5k fit** |
|---|---|---|---|---|
| description phrases | all 22 | all 22 | 21 + narrowed KB | 19 + narrowed KB (drops bare KB, AI adoption, enablement materials) |
| title exclusions on Pull B | no | yes | yes | yes |
| Pull B total (sized) | 1,569 | 1,283 | 1,059 | 739 |
| jobs/week (A+B, deduped) | ~1,775 | ~1,490 | ~1,275 | ~965 |
| **jobs/day** | **~254** | **~213** | **~182** | **~138** |
| **credits/month** | **~7,600** | **~6,400** | **~5,450** | **~4,150** |
| at spike-day volume (+10%) | ~8,300 | ~7,000 | ~6,000 | ~4,550 |
| **required plan** | 10k ($169) | 10k ($169) | 10k ($169) | 5k ($100), ~9-17% headroom |
| analysis/month, Haiku 4.5 / Sonnet 5 / Opus 5 | $42 / $84 / $209 | $35 / $70 / $175 | $30 / $60 / $150 | $23 / $46 / $114 |
| spike glads kept (of 7) | 7 | 7 | 7 | 7 |
| spike interesting jobs kept | all | all | all | all (Save the Children still reachable through "AI training program" alone, which draws 1 job/week, so it's fragile) |
| what it gives up, untested | nothing | ~41 sales/support cards/day, 0 interesting in sample | ~32/day more of bare-KB matches, 0 only-path finds in sample | ~46/day more (bare AI adoption, enablement materials, bare KB); their sampled matches (11, 10, 38) held no only-path finds, but those samples are small |

Every configuration keeps all 7 glads because the spike sample is small. **The configurations differ in untested recall.** Config D drops about 42% of Config B's description pull (1,283 → 739/week) on the strength of 59 sampled matches, and that's exactly the kind of cut the wildcard rule warns against.

## 5. Production retrieval structure (V1)

Daily and incremental, keyed on `discovered_at_gte` = the last successful run's timestamp:

1. **Pull A (titles):** `job_title_or` = every title in `search/families.yaml` `title_families`, sent as one request. This is how the 276/week was sized. No title exclusions. Per-family `must_description` filters become local tags in step 3, not retrieval filters. Applying them would take one request per family, and it would cut recall only in the two families that have them.
2. **Pull B (descriptions):** `job_description_pattern_or` = every configured description phrase. `job_title_pattern_not` = `TITLE_EXCLUDE`. `job_id_not` = Pull A's IDs from this run. A single request that combines title and description filters returns their intersection (credit log line 15: 78), so the union needs these two pulls.
3. **Combine locally**, then **re-match every stored title and description against all configured families and phrases**. Each job keeps every pattern that would have found it, which feeds `source_appearance.query_family`/`retrieval_mode`, the "why surfaced" text, and per-phrase yield tracking. Record which Pull B jobs hit only bare "knowledge base", bare "AI adoption" or "enablement materials". After 2-4 weeks, their glad count is the evidence for keeping or narrowing those phrases.
4. Page through results at the paid plan's page size. The free tier's 25-per-page and 10-per-minute limits don't shape this design.

## 6. Recommendation

**Choose Config B on the 10k plan ($169/mo).**
- **Configs A, B and C cost the same plan.** Moving from B to C saves about 32 cards/day and about $5-25/month in analysis, but it narrows a phrase for noise alone.
- **B is the broadest configuration where every cut is justified by more than volume.** The exclusions remove only sales and support titles, verified against the sample with zero glads or interesting jobs lost.
- **About 213 cards/day is more than the 100-card review budget, and that's intended** (amendment 5). Presentation handles it: order by freshness and tags (amendment 7) plus quick filters. About 45-50 of those should be interesting (≈24 from titles at 62%, ≈20-26 from descriptions once the exclusions lift their hit rate).
- **Headroom:** at spike-day volume, B uses about 7,000 of 10,000 credits. The remaining ~3,000 covers variance, a paging overlap buffer, and looser variants of the near-dead phrases.
- **Revisit after 2-4 weeks of marks**, using the per-phrase only-path tracking from §5 step 3:
  - If bare "knowledge base", "AI adoption" and "enablement materials" produce no glads, Config D would still keep everything else and allow dropping to the $100 plan.
  - If they do produce glads, stay on B.

Before buying, confirm on the paid plan that `job_title_pattern_not` accepts all 11 patterns in one request. The free-tier sizing call did (`proj_union_desc_excl`).
