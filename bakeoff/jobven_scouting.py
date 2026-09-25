"""Jobven bakeoff: scouting labels + quality metrics (no API calls).

Labels are hand-run (model_version "hand-run-reference", same rubric as
analysis/scouting.yaml v0.2-draft, including the Maryland state-allowlist rule)
for the 60-job stratified sample (bakeoff/jobven_quality_sample.json) plus the
non-sample jobs considered for cards. Reads bakeoff/jobven_jobs.jsonl; writes
bakeoff/jobven_scouting_analysis.jsonl and bakeoff/jobven_metrics.json.
"""
import collections, hashlib, json, os, re, statistics

HERE = os.path.dirname(os.path.abspath(__file__))

# id prefix: (overlap, stretch, wildcard, ai_relevance, client_ownership, workplace_in_text, suppression, note)
#   workplace_in_text: remote | unclear | hybrid | onsite | field_travel   (what the posting TEXT says)
#   suppression: None | "location_impossible: <evidence>" | "hybrid_or_onsite: <evidence>"
L = {
 # ---- title stratum: title-family replay (10)
 "fe982a40": ("strong", "some", False, "central", "none", "remote", None, "Help Center docs, Runway Academy materials, video scripts; 'open to hiring remote across the US'"),
 "c9138b14": ("strong", "big", False, "none", "supporting", "unclear", None, "agency content strategy for a financial-services client; says 'Remote (US Based)' and also 'hybrid approach including required in-office days'"),
 "15508f16": ("strong", "big", False, "adjacent", "none", "remote", None, "Neon One lead ID, custom-LMS migration, technical curricula; posted by recruiter Highlight Talent"),
 "c6643f0a": ("partial", "some", False, "central", "none", "remote", None, "part-time AI content writing; also in TheirStack spike (card 18)"),
 "c2e78a13": ("strong", "some", False, "central", "none", "unclear", None, "short video courses on AI workflows, on-camera instructor; text names office hubs, no remote statement"),
 "19c070c6": ("partial", "some", False, "none", "owns_accounts", "remote", None, "B2B SEO/content-marketing agency strategist; owns client deliverables and growth; 'future opening'"),
 "49f2e95a": ("very_low", "none", False, "none", "none", "remote", "location_impossible: must work from home in Virginia", "K-12 special-ed teacher"),
 "a2741c2e": ("very_low", "none", False, "none", "none", "field_travel", "location_impossible: Maine, monthly in-person sites", "K-12 English teacher"),
 "5333e0d2": ("very_low", "none", False, "none", "none", "remote", "location_impossible: home office in Ohio", "K-12 algebra teacher"),
 "3b24e661": ("weak", "big", False, "none", "none", "unclear", None, "API spec documentation for Quest integrations; staffing listing (Diverse Lynx)"),
 # ---- title stratum: recall title hits (20)
 "5aee02e0": ("strong", "big", False, "present", "none", "unclear", None, "eCommerce content design/UX writing, 7+ yrs; Charlotte-first 'hybrid workforce' boilerplate"),
 "17fd5f4e": ("weak", "big", False, "none", "none", "onsite", "hybrid_or_onsite: 'Onsite only', Wichita KS", "aircraft maintenance manuals; staffing (Diverse Lynx)"),
 "5c878351": ("strong", "some", False, "none", "none", "unclear", "location_impossible: listed Montreal, Canada only", "MaintainX customer education; Canadian posting"),
 "cb5c0288": ("weak", "some", False, "present", "none", "unclear", None, "Marketo lifecycle email ops"),
 "2e0c46f8": ("very_low", "some", False, "none", "none", "hybrid", "hybrid_or_onsite: onsite at Lenoir NC data center", "titled Technical Writer, actually a project manager; staffing (Diverse Lynx)"),
 "fa0f9bf0": ("weak", "none", False, "none", "none", "unclear", None, "webinar/email ops; Baltimore MD listed"),
 "f26efe3f": ("very_low", "none", False, "none", "none", "onsite", "hybrid_or_onsite: Job Corps classroom, San Marcos TX", "vocational instructor"),
 "4f8155d0": ("weak", "some", False, "none", "none", "hybrid", "hybrid_or_onsite: commuting distance to Tarrytown NY, 75% travel", "lab instrument trainer"),
 "cfc4c096": ("very_low", "none", False, "none", "none", "onsite", "hybrid_or_onsite: classroom, San Marcos TX", "reading instructor"),
 "b20c9986": ("very_low", "none", False, "none", "none", "onsite", "hybrid_or_onsite: St. Petersburg FL classroom", "ESL instructor, $20-26/hr"),
 "07416770": ("partial", "big", False, "central", "none", "onsite", "hybrid_or_onsite: 'Beautiful office in downtown San Francisco'", "content-led growth lead"),
 "f5488b09": ("strong", "some", False, "none", "none", "unclear", "location_impossible: listed Toronto, Canada only", "duplicate of 5c878351 (same text, other city)"),
 "402fb631": ("weak", "some", False, "present", "none", "unclear", None, "duplicate of cb5c0288 (ServiceNow posts one req per city)"),
 "0a6c4d91": ("strong", "some", False, "present", "none", "onsite", "hybrid_or_onsite: modern office, onsite gym, Lakewood NJ", "customer education + LXD at an MSP"),
 "f1ea4d4c": ("strong", "some", False, "none", "none", "hybrid", "hybrid_or_onsite: 'hybrid at our Tempe Corporate Office'", "higher-ed healthcare ID"),
 "901dc25e": ("weak", "some", False, "none", "none", "remote", None, "eBlast/email marketing ops; 20-30% travel"),
 "e67f05e8": ("partial", "big", False, "central", "none", "onsite", "hybrid_or_onsite: '5-6 Days In-Person', NYC", "content lead at AI startup"),
 "c6e39b2a": ("strong", "none", False, "none", "none", "unclear", None, "online course design, higher ed; Albany NY; no remote statement"),
 "24d926cf": ("partial", "some", False, "central", "none", "unclear", None, "AI-safety content lead; also in TheirStack spike (card 19)"),
 "af44ea0e": ("very_low", "some", False, "central", "none", "remote", "location_impossible: 'Located in Latin America'", "nearshore staff augmentation (Truelogic)"),
 # ---- description stratum (30)
 "d33d32b5": ("very_low", "some", False, "adjacent", "none", "unclear", None, "SRE"),
 "b4e98e47": ("weak", "big", False, "none", "none", "unclear", None, "VP sales enablement + RFP ops"),
 "89eefeb6": ("weak", "some", False, "none", "supporting", "field_travel", None, "implementation engineer; writes technical enablement materials; 20% travel"),
 "eeee6db3": ("very_low", "big", False, "adjacent", "owns_accounts", "field_travel", None, "drone solutions-engineering manager; 30% travel"),
 "2737cc57": ("partial", "some", False, "present", "none", "remote", None, "sales-enablement materials + training resources; contract $60-65/hr"),
 "ce072e90": ("weak", "some", False, "none", "none", "remote", None, "support escalation lead; some Help Center content and agent training"),
 "175d24cf": ("very_low", "big", False, "present", "owns_accounts", "field_travel", None, "partner pre-sales architect; 50% travel"),
 "88b36e14": ("very_low", "big", False, "none", "owns_accounts", "unclear", None, "sales expansion manager"),
 "c4ae6aec": ("very_low", "big", False, "adjacent", "owns_accounts", "field_travel", None, "drone SE director; 30% travel"),
 "4c20fe33": ("very_low", "big", False, "adjacent", "none", "unclear", None, "infra engineering manager"),
 "e37c2bd2": ("very_low", "big", False, "central", "supporting", "remote", None, "cloud security engineer"),
 "87ff1fac": ("very_low", "big", False, "present", "owns_accounts", "unclear", None, "enterprise deal pursuit lead"),
 "a494641c": ("very_low", "big", False, "central", "owns_accounts", "unclear", None, "Salesforce delivery manager; 25% travel"),
 "4b52fbd6": ("weak", "big", False, "present", "none", "unclear", None, "internal dev-experience PM; mentions AI adoption, knowledge management"),
 "13f3fc11": ("weak", "big", False, "adjacent", "none", "remote", None, "FS product marketing director; sales-enablement content is a slice"),
 "b25e59b2": ("weak", "big", False, "central", "none", "unclear", None, "product marketing lead"),
 "466b30bf": ("partial", "some", False, "present", "none", "unclear", None, "revenue enablement programs, certifications; 'stipends for hybrid work'"),
 "6a458b7a": ("very_low", "big", False, "present", "owns_accounts", "unclear", None, "duplicate of 87ff1fac"),
 "a8b9467b": ("very_low", "big", False, "adjacent", "none", "unclear", None, "SVP revenue operations"),
 "8a60545f": ("very_low", "none", False, "none", "none", "remote", None, "tech support $20-25/hr (local TITLE_EXCLUDE would drop it)"),
 "f7e0efaa": ("very_low", "some", False, "adjacent", "none", "unclear", None, "sales operations"),
 "bb6400bd": ("very_low", "big", False, "none", "owns_accounts", "field_travel", None, "EP mapping clinical specialist; reside in territory, drive 25-50%"),
 "b6944ddd": ("partial", "some", False, "present", "supporting", "remote", None, "customer technical enablement: webinars, workshops, reusable education content; also in TheirStack sizing sample"),
 "8110e4d6": ("very_low", "big", False, "central", "none", "remote", None, "AI SDLC engineer"),
 "1c741e62": ("very_low", "big", False, "central", "owns_accounts", "unclear", None, "AI consulting client principal"),
 "4e6ee18a": ("very_low", "big", False, "present", "owns_accounts", "unclear", None, "customer success executive, federal"),
 "15353f11": ("very_low", "big", False, "none", "supporting", "remote", None, "red team consultant"),
 "a840d289": ("very_low", "big", False, "none", "supporting", "unclear", None, "SAP Basis admin"),
 "990939a9": ("very_low", "some", False, "none", "owns_accounts", "remote", None, "enterprise renewals"),
 "54dc5dee": ("weak", "big", False, "central", "none", "unclear", None, "product marketing, advertising"),
 # ---- non-sample jobs reviewed as card candidates
 "0f6b2a78": ("strong", "some", False, "present", "none", "remote", None, "scaled customer education; remote US except SF Bay, NYC and DC metros"),
 "644e5795": ("strong", "big", False, "present", "none", "remote", None, "Senior Director client education; also in TheirStack sizing sample"),
 "fd47785f": ("strong", "some", False, "present", "none", "unclear", None, "internal product training, role-based learning paths"),
 "5af73c33": ("strong", "some", True, "present", "none", "unclear", None, "sales onboarding curricula, certifications, content library"),
 "1c4f636b": ("strong", "big", True, "present", "none", "remote", None, "revenue enablement learning programs; curriculum development; 5-7 yrs"),
 "fca7449d": ("partial", "big", True, "present", "none", "unclear", None, "technical enablement: playbooks, troubleshooting guides, sessions"),
 "bb8b1f47": ("partial", "big", True, "present", "none", "remote", None, "product enablement: training, certification paths, collateral"),
 "edc540da": ("partial", "some", False, "none", "none", "unclear", None, "Docebo LMS admin, manages learning content"),
 "42c9ea18": ("partial", "big", True, "present", "none", "unclear", None, "community publishing ops, self-service publishing training/docs"),
 "7255a2b8": ("partial", "big", False, "present", "none", "remote", None, "sales learning paths, playbooks, certifications; 8+ yrs"),
 "4fa3daf7": ("very_low", "none", False, "none", "none", "remote", "location_impossible: 'following states: California, Arizona, Colorado, Florida, Georgia, Illinois, Nevada, North Carolina, Oregon, Texas, Utah and Washington' (no MD)", "clinical quality specialist"),
}

# Staffing / recruiter / staff-augmentation relistings (employer hidden or not the hiring company)
STAFFING = {"diverse lynx", "highlightta.com", "truelogic.io"}

def full_id(prefix, ids):
    m = [i for i in ids if i.startswith(prefix)]
    assert len(m) == 1, (prefix, m)
    return m[0]

def main():
    jobs = {j["id"]: j for j in map(json.loads, open(os.path.join(HERE, "jobven_jobs.jsonl"), encoding="utf-8"))}
    sample = json.load(open(os.path.join(HERE, "jobven_quality_sample.json")))
    overlap_ts = json.load(open(os.path.join(HERE, "jobven_ts_overlap.json")))
    rows = []
    for p, (ov, st, wc, ai, co, wp, sup, note) in L.items():
        jid = full_id(p, jobs)
        j = jobs[jid]
        in_ts = jid in overlap_ts and not jid.startswith("fc303a23")  # fc303a23: substring title match to a different req
        rows.append({"job_id": jid, "analysis_version": "v0.2-draft", "model_version": "hand-run-reference",
                     "title": j["title"], "company": j["company"], "stratum": j["stratum"],
                     "in_quality_sample": jid in sample["title"] + sample["description"],
                     "sample_stratum": "title" if jid in sample["title"] else "description" if jid in sample["description"] else None,
                     "overlap": ov, "stretch": st, "wildcard": wc, "ai_relevance": ai, "client_ownership": co,
                     "workplace_in_text": wp, "remoteType": j["remoteType"], "suppression": sup, "note": note,
                     "interesting": ov in ("strong", "partial") and not sup,
                     "staffing": j["company"].lower() in STAFFING, "in_theirstack_raw": in_ts,
                     "apply_kind": j["apply_kind"], "applyUrl": j["applyUrl"], "posted": j["posted"], "desc_len": j["desc_len"]})
    with open(os.path.join(HERE, "jobven_scouting_analysis.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    S = [r for r in rows if r["in_quality_sample"]]
    assert len(S) == 60, len(S)
    def dist(rs, k):
        return dict(collections.Counter(r[k] for r in rs))
    rt_remote = [r for r in S if r["remoteType"] == "remote"]
    agree = sum(1 for r in S if (r["remoteType"] == r["workplace_in_text"]) or (r["remoteType"] == "flexible" and r["workplace_in_text"] == "unclear"))
    lens = [jobs[r["job_id"]]["desc_len"] for r in S]
    all_jobs = list(jobs.values())
    html_leak = [j["id"] for j in all_jobs if re.search(r"<(div|p|li|ul|h\d|span|strong)\b", j["description"])]
    # duplicates: same normalized company + description body
    def h(j):
        return hashlib.sha1((re.sub(r"\W", "", j["company"].lower()) + re.sub(r"\s+", " ", j["description"])[:4000]).encode()).hexdigest()
    groups = collections.defaultdict(list)
    for j in all_jobs:
        groups[h(j)].append(j["id"])
    dup_groups = [g for g in groups.values() if len(g) > 1]
    s_ids = {r["job_id"] for r in S}
    s_groups = collections.defaultdict(list)
    for j in all_jobs:
        if j["id"] in s_ids:
            s_groups[h(j)].append(j["id"])
    m = {
        "n_sample": len(S),
        "overlap_by_stratum": {s: dist([r for r in S if r["sample_stratum"] == s], "overlap") for s in ("title", "description")},
        "interesting_by_stratum": {s: sum(r["interesting"] for r in S if r["sample_stratum"] == s) for s in ("title", "description")},
        "suppressed_by_stratum": {s: sum(bool(r["suppression"]) for r in S if r["sample_stratum"] == s) for s in ("title", "description")},
        "remoteType_dist": dist(S, "remoteType"),
        "text_when_remoteType_remote": dist(rt_remote, "workplace_in_text"),
        "n_remoteType_remote": len(rt_remote),
        "remote_field_text_agreement": f"{agree}/{len(S)}",
        "desc_len": {"min": min(lens), "median": statistics.median(lens), "p90": sorted(lens)[int(0.9 * len(lens)) - 1], "under_1000": sum(l < 1000 for l in lens)},
        "html_markup_leak_all_190": len(html_leak),
        "html_markup_leak_sample": sum(1 for r in S if r["job_id"] in html_leak),
        "apply_kind_sample": dist(S, "apply_kind"),
        "apply_major_board_all": sum(j["apply_kind"] == "major_board" for j in all_jobs),
        "staffing_sample": sum(r["staffing"] for r in S),
        "staffing_all": sum(j["company"].lower() in STAFFING for j in all_jobs),
        "dup_groups_all": [[jobs[i]["company"] + " | " + jobs[i]["title"] for i in g] for g in dup_groups],
        "dup_extra_rows_all": sum(len(g) - 1 for g in dup_groups),
        "dup_extra_rows_sample": sum(len(g) - 1 for g in s_groups.values() if len(g) > 1),
        "salary_present_all": sum(bool(j["salary"]) for j in all_jobs),
        "n_all": len(all_jobs),
        "interesting_all_labeled": [(r["company"], r["title"], r["in_theirstack_raw"]) for r in rows if r["interesting"]],
    }
    json.dump(m, open(os.path.join(HERE, "jobven_metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(m, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
