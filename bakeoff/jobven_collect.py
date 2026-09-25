"""Flatten every job Jobven delivered in this bakeoff (all phases) into
bakeoff/jobven_jobs.jsonl, one row per unique job id, with every call that delivered it."""
import glob, html, json, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
MAJOR = ("linkedin.com", "indeed.com")
ATS = {"greenhouse": "greenhouse", "lever.co": "lever", "ashbyhq": "ashby", "myworkday": "workday", "smartrecruiters": "smartrecruiters",
       "workable": "workable", "icims": "icims", "ultipro": "ultipro", "ukg.net": "ukg", "bamboohr": "bamboohr", "jobvite": "jobvite",
       "dayforcehcm": "dayforce", "paylocity": "paylocity", "jobdiva": "jobdiva", "saashr": "saashr", "rippling": "rippling",
       "recruitee": "recruitee", "breezy": "breezy", "jazzhr": "jazzhr", "applytojob": "jazzhr", "successfactors": "successfactors",
       "oraclecloud": "oracle", "taleo": "taleo", "adp.com": "adp", "teamtailor": "teamtailor", "pinpointhq": "pinpoint", "dover.com": "dover"}

def url_kind(u):
    u = (u or "").lower()
    if not u:
        return "none"
    if any(m in u for m in MAJOR):
        return "major_board"
    for k, v in ATS.items():
        if k in u:
            return "ats:" + v
    return "employer_site"

def plain(h):
    t = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", h or "")
    return html.unescape(re.sub(r"<[^>]+>", " ", t))

def main():
    jobs = {}
    for fn in sorted(glob.glob(os.path.join(HERE, "raw", "jobven_*.json"))):
        d = json.load(open(fn, encoding="utf-8"))
        if "call_id" not in d or not d["url"].split("?")[0].endswith("/v1/public/jobs"):
            continue
        for j in (d["response"] or {}).get("data") or []:
            rec = jobs.setdefault(j["id"], {"job": j, "calls": []})
            rec["calls"].append(d["call_id"])
            if len(j.get("description") or j.get("descriptionPlain") or "") > len(rec["job"].get("description") or rec["job"].get("descriptionPlain") or ""):
                rec["job"] = j
    with open(os.path.join(HERE, "jobven_jobs.jsonl"), "w", encoding="utf-8") as f:
        for jid, rec in jobs.items():
            j = rec["job"]
            desc = j.get("descriptionPlain") or plain(j.get("description"))
            calls = rec["calls"]
            stratum = ("title_family" if any(c.startswith("fam_title") for c in calls) else
                       "description_family" if any(c.startswith("fam_desc") for c in calls) else
                       "recall_title" if any(c.startswith("rec_") for c in calls) else "semantics")
            f.write(json.dumps({
                "id": jid, "title": j["title"], "company": j["companies"][0]["name"], "company_website": j["companies"][0].get("website"),
                "stratum": stratum, "calls": calls, "remoteType": j.get("remoteType"),
                "locations": j.get("locations"), "posted": datetime.datetime.fromtimestamp(j["postedAt"], datetime.UTC).strftime("%Y-%m-%d") if j.get("postedAt") else None,
                "applyUrl": j.get("applyUrl"), "apply_kind": url_kind(j.get("applyUrl")), "status": j.get("status"),
                "salary": j.get("salary"), "employmentType": j.get("employmentType"), "experienceLevel": j.get("experienceLevel"),
                "requiresTravel": j.get("requiresTravel"), "travelPercentage": j.get("travelPercentage"),
                "summary": j.get("summary"), "desc_len": len(desc), "description": desc,
            }, ensure_ascii=False) + "\n")
    print(len(jobs), "unique jobs")

if __name__ == "__main__":
    main()
