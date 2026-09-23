# Mo Money: Spike Results + First Card Review

This is for GPT to pressure-test before we choose the production architecture. The design principles from the reframe (amendments 1–6 in `docs/reframe.md`) still hold; nothing below reopens them.

## What we ran

TheirStack source spike. Filters: US, remote, last 7 days. It used 150 of the 200 free credits and sampled 144 jobs across title families, description families, and a "wildcard pool" (description phrase match plus a non-obvious title). One scouting note per job was hand-run as the reference. All raw responses are saved, so we can re-analyze without re-fetching.

## Spike findings (short)

- **TheirStack works as the retrieval backbone.** Descriptions are complete (median ~5.9k chars, min 1.5k). Description regex search works (`job_description_pattern_or`), which was the key open question.
- **It mostly re-serves LinkedIn/Indeed.** 80% of sampled jobs came from those two boards. Source novelty is somewhere between 15% and 40%, and that's an upper bound because TheirStack records one source per job.
- **Title vs description retrieval:**

  | | title families | description families | wildcard pool |
  |---|---:|---:|---:|
  | jobs/day (US remote) | ~45 | ~242 | ~205 |
  | interesting in sample | 62% | 12% | 6% |

  All 5 interesting wildcards came from description search. Four description phrase groups went 0 for 40, but two of the best wildcards came from inside those same groups.
- **Data-quality problems the analysis step has to absorb:**
  - TheirStack's remote flag is unreliable: only 48% of "remote" jobs say remote in the text, 14% are travel-heavy field territories, and 9% are onsite.
  - 19% are staffing-firm relistings that hide the employer.
  - Only 41% carry a real employer/ATS apply link.
  - 5.6% are duplicates, including one filed under company "Work From Home". Duplicate matching needs a description hash, not just (company, title).
- **Free counting doesn't exist.** A count costs credits like a search. The free plan allows 25 results per page and 10 requests per minute.

## Cost at full scale (monthly)

| configuration | jobs/day | TheirStack plan | scouting analysis |
|---|---:|---:|---:|
| all families as written | ~276 | $169 (10k credits) | ~$46 cheap model, up to ~$228 top model |
| title + tightened description phrases (estimate) | ~100–120 | $100 (5k credits) | ~$18 to ~$91 |

## Rone's card review (20 cards)

| result | cards |
|---|---|
| **Glad I saw this** | 5, 7, 10, 12, 14, 15, 17 (7) |
| Already found myself | 4 (1) |
| Stretch too big | 2 (Director-level role, program ownership, hiring) |
| Card was wrong | 1: missed a Maryland eligibility restriction |
| Filtered correctly | 20: Maryland excluded (included on purpose to test the rule) |
| Unmarked | neutral, not negative |

**What the marks say:**

1. **7 of 18 eligible cards were glad, and only 1 was already known.** That's early evidence Mo Money finds things Rone wouldn't.
2. **All 7 glads were on LinkedIn or Indeed.** The value right now is *attention novelty*: jobs on boards he uses that he'd never have searched for or noticed. It is not access to new sources.
3. **2 of the 7 glads came from description search.** #5 was BCBS NC's "Senior Digital Product Analyst", which is actually content-governance work. #15 was Shipley. Title search alone would have missed both.
4. **A big stretch didn't reduce interest.** Two glads were flagged big stretch. "Too big" triggered only on Director plus people management, and that's one data point.
5. **AI-central wasn't predictive:** 1 glad out of 6 AI-central cards. That's consistent with AI being a differentiator, not a requirement.
6. **Glad ≠ would apply.** Rone passed on #5 and #12 after reading deeper, but they still count as successful finds. This is now amendment 6: not applying is a neutral signal and never feeds exclusions or ordering.
7. **The eligibility logic had a real bug.** The analysis caught Maryland only when a posting named it. It missed "hires in these states only" lists that don't include MD (Springboard, Bryan University). That's fixed in the spec, and a re-scan found no other misses.

## Claude's recommendations

1. **TheirStack is the primary source for V1, and the only source for now.** The glads show the value is attention novelty on boards TheirStack already covers. Defer direct ATS/careers-page ingestion and the SerpAPI cross-check until 2–4 weeks of live marks show whether off-board jobs ever turn into glads.
2. **Keep description search broad and cut only obvious junk.** For example, bare "knowledge base" brings in about 650 help-desk jobs a week, and a `job_title_not` filter can drop sales and support titles. Don't tighten down to ~100/day: the wildcard wins came from exactly the phrases a hard tightening would cut. That probably means the $169 plan. Use the remaining 50 credits to size each phrase first; if the pruned set comes in under 5k credits a month, the $100 plan works.
3. **Make eligibility deterministic where possible.** Location and state restrictions caused the only card error. Pair the model's reading with a rules check (state-list patterns, onsite/hybrid phrases) and a regression set built from the spike jobs, so this can't silently break again.
4. **Choose the analysis model by agreement, not price.** Run the cheap model against the 144 reference notes, and only use it if its overlap, stretch and wildcard tags and its eligibility calls match closely. Skip the batch discount, because a 24-hour delay hurts freshness.
5. **Minimal V1:** daily TheirStack pull (incremental on `discovered_at`) → description-hash dedupe → eligibility check + scouting note → one feed in a Google Sheet (a Drive connector is available) → card-level marks (glad / saved / stretch too big / dismissed) → ordering nudged by marks, never filtered.

## Questions for GPT

1. Is "TheirStack alone for V1, defer ATS-direct" right given that 7 of 7 glads were on-board? Or is that sample too small to deprioritize source novelty?
2. Does the $169-plan wide net hold up, or is there a smarter way to keep wildcard recall at lower volume (for example, rotating description phrases across days)?
3. Is a Google Sheet a good enough V1 feed, or does the tag, filter and card-mark workflow need a small web page from day one?
4. Anything in the minimal V1 that's premature, or anything missing that will hurt in week 2?
