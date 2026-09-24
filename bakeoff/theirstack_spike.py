"""TheirStack source spike runner (one-off, not production ingestion).

Every call is logged to bakeoff/raw/credit_log.jsonl with credits spent
(measured from the credit-balance endpoint before/after), and every raw
response is saved to bakeoff/raw/<query_id>.json so nothing is re-fetched.

Usage: python bakeoff/theirstack_spike.py <phase>   (phase = size | sample)
"""
import json, os, re, sys, time, urllib.request, urllib.error

API = "https://api.theirstack.com"
KEY = os.environ["THEIRSTACK_API_KEY"]
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
LOG = os.path.join(RAW, "credit_log.jsonl")
RESERVE = 5  # was 40 during the spike; the projection pass may spend the rest on sizing

# Rone's declared constraint: 100% remote. Country US because a Maryland
# resident can't take roles restricted to other countries. MD-excluded
# postings can't be filtered at retrieval; the scouting pass flags them.
BASE = {
    "posted_at_max_age_days": 7,
    "job_country_code_or": ["US"],
    "workplace_types_or": ["remote"],
}

def ci(phrases):
    return ["(?i)" + p for p in phrases]

TITLE_FAMILIES = {
    "content_dev": (["content developer", "content designer", "content strategist", "content development manager", "content lead"], []),
    "instructional_lxd": (["instructional designer", "learning experience designer", "LXD", "learning designer", "e-learning developer"], []),
    "curriculum_training": (["curriculum developer", "curriculum designer", "curriculum manager", "training developer", "training content"], []),
    "enablement_education": (["enablement content", "sales enablement content", "customer education", "customer education content", "academy"],
                             [r"(?i)\bcontent\b", r"(?i)\bcourses?\b", r"(?i)\bcurriculum\b", r"(?i)\blearning\b"]),
    "technical_content": (["technical content", "technical writer", "developer education", "documentation lead", "content engineer"],
                          [r"\bAI\b", r"\bLLMs?\b", r"(?i)machine learning", r"(?i)generative"]),  # AI/LLM case-sensitive on purpose
    "ai_learning": (["AI enablement", "AI adoption", "AI learning", "AI education", "AI trainer", "AI literacy", "AI content"], []),
}

DESC_FAMILIES = {
    "course_content": ["develop(ing)? course content", "course development", "learning content", "e-learning content"],
    "curriculum": ["curriculum development", "design(ing)? (the )?curriculum", "training curriculum"],
    "enablement_material": ["enablement materials", "enablement content", "playbooks and training"],
    "customer_training": ["customer training", "customer education", "onboarding content", "academy content"],
    "knowledge_content": ["knowledge base", "help center content", "content operations", "content governance"],
    "ai_adoption": ["AI adoption", "AI literacy", "AI training program", "teach teams to use AI"],
}

# Conservative title exclusions for description retrieval (Pull B): obvious sales, support,
# help-desk and customer-success roles. Regex (job_title_pattern_not), not job_title_not:
# job_title_not is bag-of-words, so "customer success manager" would also drop
# "Customer Success Content & Enablement Manager". Every phrase here needs its words adjacent.
TITLE_EXCLUDE = {
    "account_exec":     r"(?i)\baccount executive",
    "account_manager":  r"(?i)\b(key |partner |strategic |enterprise |technical )?account manager",
    "sales_rep":        r"(?i)\bsales (representative|rep|executive|associate|consultant|specialist)\b",
    "sales_mgmt":       r"(?i)(\bsales (manager|director)\b|\bdirector,? (of )?sales\b|\b(vp|vice president),? (of )?sales\b|\bhead of sales\b)",
    "sales_dev":        r"(?i)(\bsales development\b|\b(sdr|bdr)\b|\bbusiness development (representative|rep|executive|manager)\b)",
    "territory":        r"(?i)\bterritory (manager|representative|sales)\b",
    "presales_eng":     r"(?i)(\b(solutions?|sales) engineer\b|\bpre-?sales\b|\bsolutions consultant\b)",
    "cust_service":     r"(?i)\bcustomer (service|support|care) (representative|rep|agent|associate|advocate|specialist)\b",
    "tech_support":     r"(?i)\b(technical|tech|it|application|desktop) support (specialist|analyst|technician|representative|rep|engineer)\b",
    "help_desk":        r"(?i)(\bhelp ?desk\b|\bservice desk\b|\btier (1|2|3|i|ii|iii) support\b|\bcall cent(er|re) (agent|representative)\b)",
    "cust_success":     r"(?i)\b(customer|client) success (manager|associate|representative|executive)\b",
}

# Narrowed "knowledge base": someone writes/builds/owns KB content, not just uses a KB.
NARROW_KB = (r"(knowledge[- ]base (articles?|content)|(writ|build|creat|develop|maintain|own|curat)\w* (and \w+ )?"
             r"(an? |the |our )?(internal |external |customer[- ]facing )?knowledge[- ]base)")

# Titles that a title-family search would already catch. Excluding them from a
# description search isolates the jobs only description retrieval can find.
OBVIOUS_TITLE = r"(?i)(content|instructional|learning|curriculum|training|trainer|enablement|educat|writer|documentation|course|academy|\bLXD\b)"

def title_q(fid):
    titles, must = TITLE_FAMILIES[fid]
    q = dict(BASE, job_title_or=titles)
    if must:
        q["job_description_pattern_or"] = must
    return q

def desc_q(fid):
    return dict(BASE, job_description_pattern_or=ci(DESC_FAMILIES[fid]))

ALL_TITLES = sorted({t for ts, _ in TITLE_FAMILIES.values() for t in ts})
ALL_DESC = ci([p for ps in DESC_FAMILIES.values() for p in ps])

def queries_size():
    qs = {}
    for f in TITLE_FAMILIES:
        qs[f"size_title_{f}"] = ("title_family", f, title_q(f))
    for f in DESC_FAMILIES:
        qs[f"size_desc_{f}"] = ("description_family", f, desc_q(f))
    qs["size_union_title"] = ("title_family", "ALL", dict(BASE, job_title_or=ALL_TITLES))
    qs["size_union_desc"] = ("description_family", "ALL", dict(BASE, job_description_pattern_or=ALL_DESC))
    qs["size_overlap_title_and_desc"] = ("title_family", "ALL∩desc", dict(BASE, job_title_or=ALL_TITLES, job_description_pattern_or=ALL_DESC))
    qs["size_wildcard_desc_not_obvious_title"] = ("description_family", "wildcard", dict(BASE, job_description_pattern_or=ALL_DESC, job_title_pattern_not=[OBVIOUS_TITLE]))
    no_remote = {k: v for k, v in BASE.items() if k != "workplace_types_or"}
    qs["size_union_title_any_workplace"] = ("title_family", "ALL/any-workplace", dict(no_remote, job_title_or=ALL_TITLES))
    return qs

def http(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())

def balance():
    b = http("GET", "/v0/billing/credit-balance")
    return b["api_credits"] - b["used_api_credits"]

def seen_ids():
    ids = set()
    for fn in os.listdir(RAW):
        if fn.endswith(".json"):
            for j in json.load(open(os.path.join(RAW, fn), encoding="utf-8")).get("response", {}).get("data", []):
                ids.add(j["id"])
    return ids

def run(qid, mode, family, filters, limit, totals, exclude_seen=False):
    out = os.path.join(RAW, qid + ".json")
    if os.path.exists(out):
        print(f"skip {qid} (already fetched)")
        return
    body = dict(filters, limit=limit, include_total_results=totals,
                order_by=[{"field": "date_posted", "desc": True}])
    if exclude_seen:
        ids = sorted(seen_ids())
        if ids:
            body["job_id_not"] = ids
    time.sleep(20)  # free plan: 10 requests/minute, balance checks included
    before = balance()
    if before - limit < RESERVE:
        print(f"STOP {qid}: balance {before} would drop below reserve {RESERVE}")
        sys.exit(1)
    t0 = time.time()
    try:
        resp = http("POST", "/v1/jobs/search", body)
    except urllib.error.HTTPError as e:
        print(f"ERROR {qid}: {e.code} {e.read()[:500]}")
        return
    after = balance()
    rec = {"query_id": qid, "retrieval_mode": mode, "family": family, "limit": limit,
           "returned": len(resp.get("data", [])), "total_results": resp.get("metadata", {}).get("total_results"),
           "credits_before": before, "credits_after": after, "credits_spent": before - after,
           "seconds": round(time.time() - t0, 1), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    json.dump({"query_id": qid, "retrieval_mode": mode, "family": family, "request": body, "response": resp},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    phase = sys.argv[1]
    if phase == "size":
        for qid, (mode, fam, flt) in queries_size().items():
            run(qid, mode, fam, flt, limit=1, totals=True)
    elif phase == "offboard":
        # Source novelty sizing: same unions, excluding jobs TheirStack saw on LinkedIn/Indeed.
        nb = {"url_domain_not": ["linkedin.com", "indeed.com"]}
        run("size_offboard_union_title", "title_family", "ALL/off-board", dict(BASE, job_title_or=ALL_TITLES, **nb), limit=1, totals=True)
        run("size_offboard_union_desc", "description_family", "ALL/off-board", dict(BASE, job_description_pattern_or=ALL_DESC, **nb), limit=1, totals=True)
    elif phase == "project":
        # Sizing only (limit 1 + totals) for docs/credit-projection.md. Likely-junk phrases first.
        first = ["knowledge base", "customer training", "customer education", "AI adoption", "onboarding content", "playbooks and training"]
        rest = [p for ps in DESC_FAMILIES.values() for p in ps if p not in first]
        for p in first + rest:
            qid = "proj_phrase_" + re.sub(r"\W+", "_", p).strip("_").lower()
            run(qid, "description_family", p, dict(BASE, job_description_pattern_or=ci([p])), limit=1, totals=True)
        excl = list(TITLE_EXCLUDE.values())
        narrow = [p for p in ALL_DESC if p != "(?i)knowledge base"] + ["(?i)" + NARROW_KB]
        for qid, fam, flt in [
            ("proj_union_title_sameday", "ALL", dict(BASE, job_title_or=ALL_TITLES)),
            ("proj_union_desc_sameday", "ALL", dict(BASE, job_description_pattern_or=ALL_DESC)),
            ("proj_union_desc_excl", "ALL+title_exclude", dict(BASE, job_description_pattern_or=ALL_DESC, job_title_pattern_not=excl)),
            ("proj_phrase_knowledge_base_excl", "knowledge base+title_exclude", dict(BASE, job_description_pattern_or=ci(["knowledge base"]), job_title_pattern_not=excl)),
            ("proj_phrase_knowledge_base_narrow", "knowledge base (narrow)", dict(BASE, job_description_pattern_or=["(?i)" + NARROW_KB])),
            ("proj_union_desc_narrowkb_excl", "ALL (narrow kb)+title_exclude", dict(BASE, job_description_pattern_or=narrow, job_title_pattern_not=excl)),
        ]:
            run(qid, "title_family" if "title" in qid else "description_family", fam, flt, limit=1, totals=True)
    elif phase == "sample":
        plan = json.load(open(os.path.join(HERE, "sample_plan.json")))
        for qid, spec in plan.items():
            if spec["kind"] == "title":
                flt = title_q(spec["family"]); mode = "title_family"
            elif spec["kind"] == "desc":
                flt = desc_q(spec["family"]); mode = "description_family"
            else:
                flt = dict(BASE, job_description_pattern_or=ALL_DESC if spec["family"] == "ALL" else ci(DESC_FAMILIES[spec["family"]]),
                           job_title_pattern_not=[OBVIOUS_TITLE]); mode = "description_family"
            run(qid, mode, spec["family"], flt, limit=spec["limit"], totals=False, exclude_seen=True)
