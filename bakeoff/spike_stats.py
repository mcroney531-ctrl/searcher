"""Flatten raw TheirStack responses into bakeoff/jobs_sample.jsonl and print spike stats.
Reads only bakeoff/raw/; never calls the API."""
import json, os, re, collections
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

MAJOR = ("linkedin.com", "indeed.com")
ATS = {"greenhouse.io": "greenhouse", "lever.co": "lever", "ashbyhq.com": "ashby", "myworkdayjobs.com": "workday",
       "workday.com": "workday", "icims.com": "icims", "smartrecruiters.com": "smartrecruiters", "jobvite.com": "jobvite",
       "bamboohr.com": "bamboohr", "workable.com": "workable", "paylocity.com": "paylocity", "ultipro.com": "ukg",
       "ukg.com": "ukg", "adp.com": "adp", "taleo.net": "taleo", "successfactors.com": "successfactors",
       "oraclecloud.com": "oracle", "rippling.com": "rippling", "breezy.hr": "breezy", "jazzhr.com": "jazzhr",
       "applytojob.com": "jazzhr", "recruitee.com": "recruitee", "teamtailor.com": "teamtailor", "dayforcehcm.com": "dayforce",
       "paycomonline.net": "paycom", "gusto.com": "gusto", "pinpointhq.com": "pinpoint", "eightfold.ai": "eightfold",
       "phenompeople.com": "phenom", "trinethire.com": "trinet", "hire.trakstar.com": "trakstar", "careers-page.com": "careers-page"}

def dom(u):
    if not u:
        return None
    h = urlparse(u).netloc.lower()
    return h[4:] if h.startswith("www.") else h

def classify(u, company_domain):
    d = dom(u)
    if not d:
        return "none"
    if any(d == m or d.endswith("." + m) for m in MAJOR):
        return "major_board"
    for k, v in ATS.items():
        if d == k or d.endswith("." + k):
            return "ats:" + v
    if company_domain and (d == company_domain or d.endswith("." + company_domain)):
        return "company_site"
    return "other:" + d

def norm_title(t):
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\(.*?\)|-.*remote.*|,? ?remote", "", t.lower())).strip()

jobs, appearances = {}, collections.defaultdict(list)
log = [json.loads(l) for l in open(os.path.join(RAW, "credit_log.jsonl"), encoding="utf-8")]
for fn in sorted(os.listdir(RAW)):
    if not fn.endswith(".json"):
        continue
    r = json.load(open(os.path.join(RAW, fn), encoding="utf-8"))
    if r["query_id"].startswith("size_offboard"):
        continue  # count-only novelty queries, run after the scouting pass
    for j in r["response"]["data"]:
        appearances[j["id"]].append(r["query_id"])
        if j["id"] in jobs:
            continue
        desc = j.get("description") or ""
        cd = j.get("company_domain")
        jobs[j["id"]] = {
            "id": j["id"], "query_id": r["query_id"], "retrieval_mode": r["retrieval_mode"], "family": r["family"],
            "stratum": "wildcard" if "wildcard" in r["query_id"] else r["retrieval_mode"],
            "title": j["job_title"], "company": j.get("company"), "company_domain": cd,
            "industry": (j.get("company_object") or {}).get("industry"),
            "employees": (j.get("company_object") or {}).get("employee_count"),
            "url": j.get("url"), "final_url": j.get("final_url"), "source_url": j.get("source_url"),
            "url_kind": classify(j.get("url"), cd), "final_kind": classify(j.get("final_url"), cd),
            "source_kind": classify(j.get("source_url"), cd),
            "location": j.get("location"), "remote": j.get("remote"), "hybrid": j.get("hybrid"),
            "salary": j.get("salary_string"), "seniority": j.get("seniority"), "date_posted": j.get("date_posted"),
            "discovered_at": j.get("discovered_at"), "reposted": j.get("reposted"), "easy_apply": j.get("easy_apply"),
            "employment": j.get("employment_statuses"), "desc_len": len(desc), "description": desc,
        }

for jid, qs in appearances.items():
    jobs[jid]["appeared_in"] = qs

with open(os.path.join(HERE, "jobs_sample.jsonl"), "w", encoding="utf-8") as f:
    for j in jobs.values():
        f.write(json.dumps(j, ensure_ascii=False) + "\n")

J = list(jobs.values())
n = len(J)
C = collections.Counter
print("credits spent:", sum(r["credits_spent"] for r in log), "calls:", len(log), "jobs returned:", sum(r["returned"] for r in log), "unique ids:", n)
print("ids in >1 query:", sum(1 for q in appearances.values() if len(q) > 1))
dup = C((j["company"], norm_title(j["title"])) for j in J)
print("same company+normalized title, different id:", {k: v for k, v in dup.items() if v > 1})
print("source_kind:", C(j["source_kind"].split(":")[0] for j in J).most_common())
print("source detail:", C(j["source_kind"] for j in J).most_common(25))
print("url_kind:", C(j["url_kind"].split(":")[0] for j in J).most_common())
print("final_url present:", sum(1 for j in J if j["final_url"]), "final_kind:", C(j["final_kind"].split(":")[0] for j in J).most_common())
apply_ok = sum(1 for j in J if j["final_kind"].split(":")[0] in ("ats", "company_site") or j["url_kind"].split(":")[0] in ("ats", "company_site"))
print("real company/ATS apply URL available:", apply_ok, "/", n)
L = sorted(j["desc_len"] for j in J)
print("desc len min/p10/median/p90/max:", L[0], L[n // 10], L[n // 2], L[9 * n // 10], L[-1], "under 1000 chars:", sum(1 for x in L if x < 1000))
print("salary present:", sum(1 for j in J if j["salary"]), "reposted:", sum(1 for j in J if j["reposted"]), "easy_apply:", sum(1 for j in J if j["easy_apply"]))
print("remote true:", sum(1 for j in J if j["remote"]), "hybrid true:", sum(1 for j in J if j["hybrid"]))
print("seniority:", C(j["seniority"] for j in J).most_common())
print("employment:", C(tuple(j["employment"] or []) for j in J).most_common())
print("posted dates:", C(j["date_posted"] for j in J).most_common())
md = [j for j in J if re.search(r"Maryland|\bMD\b", j["description"])]
print("mentions Maryland/MD:", [(j["id"], j["title"]) for j in md])
st = [j for j in J if re.search(r"(?i)(eligible|able to|authorized to|can) (hire|employ)|following states|states? (listed|where)|not (able|eligible) to (hire|employ)|residen(t|cy) (of|in)", j["description"])]
print("state-eligibility language:", len(st))
for s in C(j["stratum"] for j in J).items():
    print("stratum", s)
