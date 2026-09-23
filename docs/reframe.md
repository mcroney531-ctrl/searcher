# Mo Money: Reframe Response

> **Amended after GPT review (accepted in full):**
> 1. **Novelty has three kinds.** *Source* (not on the usual boards), *discovery* (Mo Money surfaced it first) and *attention* (it was on a board Rone uses, but he missed it). Only source novelty is observable in the product; "on LinkedIn" is a neutral tag, not a demotion. Discovery and attention novelty are measured in the bakeoff against his manual list.
> 2. **No model-judged hard exclusions in V1.** "Unrelated profession" becomes `overlap: very_low`, shown dimmed. Only closed jobs and constraints Rone explicitly declares impossible get suppressed, logged and reversible.
> 3. **One analysis pass in V1.** A full scouting note on every job. Tag and note fields stay separate in the schema so tiering can be added later if the spike shows cost demands it.
> 4. **One feed, not lanes.** Tags on each card (STRONG OVERLAP, BIG STRETCH, WILDCARD, AI CENTRAL, OFF MAJOR BOARDS, CLIENT-FACING) plus quick filters. Sections 3-6 below that mention lanes, derived labels or two-tier inference are superseded by `schema/jobs.sql` and `analysis/scouting.yaml`.
> 5. **Review budget is not a discovery cap.** Rone's "cards I'd scan per day" sets what gets prominence first and drives the review-burden metric. It never narrows retrieval. The TheirStack free tier is for stratified bakeoff sampling (title families, description families, wildcard-prone queries); the spike projects full-volume cost instead of designing around 200 credits.
> 6. **A find counts as a success whether or not he applies.** Learning signals come from what Rone does at the card level: glad, saved, opened, stretch too big, dismissed. Deciding not to apply after reading the full posting is a neutral signal. It never produces an exclusion rule or pushes similar jobs down. Unmarked cards are neutral too. "Stretch too big" is its own signal, separate from a skip. The only hard filters are declared constraints (remote-only, Maryland eligibility).
> 7. **In V1, marks don't change the order of the feed.** Store every mark, but order by freshness and tags only, with simple display filters. Twenty cards is nowhere near enough to learn preferences; revisit once weeks of marks exist. "Glad I saw this" stays the main success signal.

Claude's response to the "scouting layer, not decision-maker" reframe. I accept the reframe. Below are the seven answers, plus three places where it changes things more than the brief implied and one internal contradiction I'd resolve differently.

## Where the reframe cuts deeper than stated

**1. Title search can't find unexpected titles.** "Surface titles I wouldn't have searched for" is impossible with title-family queries, because by definition you only get titles you listed. Discovery needs a second retrieval mode: **responsibility phrases matched against the description**, such as "develop course content", "learning content", "curriculum development", "enablement materials", "customer training" and "knowledge base". Title families give dependable volume. Description families are where the wildcards come from. I believe TheirStack supports description-pattern filters, but I couldn't confirm it because its docs are blocked from this environment, so the spike has to verify it first.

**2. The value is marginal novelty, not raw coverage.** Rone already checks LinkedIn and Indeed by hand, so a posting Mo Money finds that's also on LinkedIn is worth close to zero. What counts is the set that's absent from, or late to, the boards he already checks: jobs only on a company careers page or ATS, niche boards, reposts he skipped. That changes the bakeoff (section 7), and it demotes the LinkedIn-alert sentinel from coverage insurance to something we likely don't need. It also defuses the TheirStack 30-day repost concern: a repost inside 30 days is the same opening, and if it's on LinkedIn he sees it anyway.

**3. A wide net costs money in two places.** TheirStack bills a credit per job returned, so the free 200 a month is one day of wide-net volume. An LLM scouting note on every job adds a second per-job cost. Both scale with recall, so recall has a budget. My proposal is two-tier analysis: a cheap tagging pass on everything, and the full scouting note only for jobs that aren't Probably-not, or on demand when Rone opens a card. We need a realistic daily volume estimate from the spike before choosing a plan tier.

## The contradiction: Stretch can't be both a lane and an axis

The brief says stretch "should be represented as its own characteristic, not simply converted into a lower overall score." It then lists Stretch as a lane next to Natural fit. Those conflict. A single-select lane puts back the collapse the brief is trying to avoid, because "strong overlap and big stretch" has to pick one bucket.

Resolution: **two axes and one flag stored, with the label derived for display.**

- `overlap`: strong | partial | weak. How much of the work itself matches.
- `stretch`: none | some | big. How far the stated asks (years, ownership, domain, audience) exceed an obvious match.
- `wildcard`: bool. The title, industry or stated background is unexpected, but the responsibilities overlap.

The display label is computed, not asked of the model:

| overlap | stretch | wildcard | label |
|---|---|---|---|
| strong | none/some | no | **Strong look** |
| strong | big | no | **Stretch** (strong overlap) |
| partial | none/some | no | **Worth a look** |
| partial | big | no | **Stretch** |
| strong/partial | any | yes | **Wildcard** |
| weak | any | any | **Probably not** |

The card always shows both axes, so "Stretch" never hides the fact that the overlap is strong. Sorting never ranks a strong-overlap Stretch below a partial-overlap Worth-a-look by default (section 6).

## 1. Revised conceptual architecture

```
broad discovery (cloud, scheduled)
  ├─ title families        → volume
  └─ description families  → wildcards
        ↓
normalize + dedupe (canonical job, many source appearances)
        ↓
novelty tagging (is it on LinkedIn/Indeed? first seen where/when?)
        ↓
tier 1: cheap tag pass on everything (overlap, stretch, wildcard, hard-exclusion check)
        ↓
tier 2: scouting note (non-Probably-not jobs, or on open)
        ↓
queue (lanes, new-since-last-visit, full depth browsable)
        ↓
original posting link  ·  Chrome deep-read on demand for the few he's serious about
```

Retrieval never judges and analysis never fetches. One versioned analysis prompt covers every source. Raw descriptions are kept, so a prompt change re-runs on history without re-fetching.

## 2. Canonical job record

This is unchanged in structure from the earlier draft: `company` → `job` (one real opening) → `source_appearance` (each sighting, raw payload kept). Additions for the reframe:

- `job.novelty`: `off_major_boards` | `also_on_major_boards` | `unknown`. Derived from the source URLs seen across appearances.
- `job.first_seen_source`: where we saw it first. Answers "did Mo Money beat LinkedIn to it?"
- `source_appearance.retrieval_mode`: `title_family` | `description_family`, plus the family id and exact query. That lets us measure which modes actually produce the wildcards.
- `user_state` (new table, one row per job): `new | seen | opened | saved | dismissed | applied`, with timestamps. Feedback affects ordering only (section 6).
- `exclusion` (new table): job_id, rule_id, evidence excerpt, and an `overridden` flag. Excluded jobs stay stored and browsable.

The old `grade` table (gate / 0–4 dimension scores / rank_score) is replaced by the scouting schema below.

## 3. Scouting-analysis output schema

```yaml
analysis_version: str        # prompt/rubric version
model_version: str
tier: tag | note             # tier 1 fills the first block; tier 2 adds the rest

# tier 1: tags (every job)
role_family: str             # a known family, or free text for unexpected titles
overlap: strong | partial | weak
stretch: none | some | big
stretch_reasons: [str]       # "asks 7+ yrs", "owns enterprise program", "healthcare domain required"
wildcard: bool
ai_relevance: central | present | adjacent | none   # a differentiator, never a gate
hard_exclusion: null | {rule_id, evidence}

# tier 2: scouting note (answers "why might I care?", never "should I apply?")
why_surfaced: str            # which query/family hit, in plain words
overlap_points: [str]        # the concrete duties that match
stretch_points: [str]
caveats: [str]               # real mismatches, e.g. client ownership, travel, contract
worth_opening_because: str   # one line
missing_info: [str]          # salary, level, remote policy not stated
confidence: high | medium | low
```

There's no numeric score in the output contract. If ordering needs a number, code computes it from these fields and it never appears in the UI.

## 4. How the four lanes coexist

Covered in the contradiction section above: two axes plus a flag, with the label derived. Two more rules follow from it:

- Client or account ownership becomes a **caveat**, not a gate. It's displayed prominently because it was the mismatch that mattered in the original lens, but it doesn't remove the job.
- "Probably not" is based on weak overlap only. Stretch alone never sends a job there.

## 5. Hard exclusions (rare, logged, reversible)

These qualify:

1. **Clearly unrelated profession.** Nursing, CDL driving, retail floor and so on, where overlap is weak and there's no content or learning duty at all. This is the only broad one.
2. **Location impossible.** An onsite or hybrid-only role outside Rone's workable geography, or a country he can't work in. It needs his geography rules.
3. **Explicit work-authorization or clearance requirement** he can't meet.
4. **Closed or expired** at the source.

These **do not** qualify: seniority or years asked, missing salary, a weird title, no AI mention, client ownership, stretch of any size, or industry.

Every exclusion writes a row with the rule and an evidence excerpt to a browsable "Filtered" drawer. A weekly sample of it gets a human glance, to catch the classifier eating real jobs.

## 6. A wide-net queue that still surfaces the best

- **Lanes as tabs with counts:** Strong look · Stretch · Wildcard · Worth a look · Probably not · Filtered. Counts stay visible, so depth is always obvious and nothing is a hidden "rest".
- **Default view is "new since last visit" across all lanes,** grouped by lane, not a top-N list.
- **Within a lane, sort by freshness first,** then overlap. A three-day-old Strong look beats a two-week-old one, and job search rewards speed.
- **Exploration quota:** a fixed share of the top of the default view (say 1 in 5) is reserved for Wildcard and a random Probably-not sample. That's the filter-bubble guard, and it's structural, not a promise.
- **Feedback adjusts prominence with decay.** Opens and saves nudge similar jobs up, dismisses nudge them down, and the effect fades over weeks. Nothing ever moves a whole family or lane out of view.
- **Novelty badge:** "not on LinkedIn/Indeed" goes on the card. That's the headline value of the tool.

V1 UI: Google Sheets or a single web page. The lane logic is identical either way. Choose after the spike.

## 7. Changes to the source bakeoff

- **The primary metric changes** from found/missed plus garbage rate to **marginal novelty**: relevant jobs the source finds that Rone didn't already see, or saw later, on LinkedIn/Indeed. Coverage of LinkedIn jobs is secondary.
- **A new metric: wildcard yield.** Of the jobs Rone marks "glad I saw this", how many came from description families rather than title families.
- **The noise metric becomes review burden:** cards per day, and minutes to scan them. Garbage is tolerable at a manageable volume. Premature exclusion is the failure to measure: sample the Filtered drawer.
- **Cost gets measured, not assumed:** credits per day at wide-net volume, plus analysis cost per job, at both tiers.
- **Comparator reshuffle:** direct ATS-domain searches (Greenhouse/Lever/Ashby) move up, because off-board postings are the target. SerpAPI/Google Jobs stays as a comparator. LinkedIn-alert ingestion drops out of the bakeoff, since he covers LinkedIn himself.
- **The gold set is now two lists:** (a) jobs he already found manually over the test window, which is the baseline for novelty, and (b) his "glad I saw this" marks on Mo Money output, which is the yield.
- **The 30-day repost question is downgraded.** It only matters for off-board reposts. Check it in passing, don't design around it.

## Open inputs needed from Rone before the spike

1. Workable geography and remote policy (drives hard exclusion #2).
2. Any work-authorization or clearance constraints.
3. A rough daily card count he'd realistically scan (sets the volume and credit budget).
4. A TheirStack API key, and network access to `theirstack.com` / `api.theirstack.com` for the build environment.
