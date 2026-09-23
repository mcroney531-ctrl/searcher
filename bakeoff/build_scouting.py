"""Expand hand-run scouting rows into the analysis/scouting.yaml contract and compute spike metrics.
Writes bakeoff/scouting_analysis.jsonl and bakeoff/spike_metrics.json. No API calls."""
import json, os, re, hashlib, collections
import scouting_rows
from theirstack_spike import TITLE_FAMILIES, DESC_FAMILIES

HERE = os.path.dirname(os.path.abspath(__file__))
J = {j["id"]: j for j in (json.loads(l) for l in open(os.path.join(HERE, "jobs_sample.jsonl"), encoding="utf-8"))}
C = collections.Counter

def matched_phrase(j):
    fams = DESC_FAMILIES if j["family"] == "ALL" else {j["family"]: DESC_FAMILIES[j["family"]]}
    for f, ps in fams.items():
        for p in ps:
            m = re.search("(?i)" + p, j["description"])
            if m:
                return f, m.group(0)
    return None, None

def why(j):
    if j["stratum"] == "title_family":
        fam = j["family"]
        fam_txt = f"the '{fam}' title family" if fam in TITLE_FAMILIES else "a title-family sizing query"
        return f"Title matched {fam_txt}: \"{j['title']}\"."
    f, p = matched_phrase(j)
    lead = "Description-only find (title not an obvious content/learning title)" if j["stratum"] == "wildcard" else "Description matched"
    return f"{lead}: the posting says \"{p}\" ({f} family)." if p else f"{lead} ({j['family']})."

def missing(j, a):
    out = []
    if not j["salary"]:
        out.append("salary")
    if a["workplace"] == "unclear":
        out.append("remote policy not explicit in text")
    if not j["final_url"]:
        out.append("employer apply URL (only a LinkedIn/Indeed link)")
    if not j["employment"]:
        out.append("employment type")
    return out

# Remote roles restricted to a listed set of states that omits Maryland.
# HCA x2: must live near a hospital in listed states. Springboard: CA/FL/TX/MA/AZ/NY/IL
# (caught by Rone's card review; the spike analysis missed it). Bryan University: "reside in the following states".
MD_EXCLUDED = {850947082, 850274105, 851985369, 852327987}

def suppression(jid, a):
    if jid in MD_EXCLUDED:
        return {"rule_id": "location_impossible", "evidence": "state list for remote eligibility excludes Maryland"}
    if a["workplace"] in ("onsite", "hybrid"):
        return {"rule_id": "location_impossible", "evidence": f"posting text reads {a['workplace']}; Rone is 100% remote"}
    return None

def desc_key(j):
    return hashlib.md5(re.sub(r"\W+", "", j["description"].lower())[:1500].encode()).hexdigest()

rows = []
for jid, a in scouting_rows.R.items():
    j = J[jid]
    s = suppression(jid, a)
    tags = [t for t, ok in [("STRONG OVERLAP", a["overlap"] == "strong"), ("BIG STRETCH", a["stretch"] == "big"),
                            ("WILDCARD", a["wildcard"]), ("AI CENTRAL", a["ai_relevance"] == "central"),
                            ("OFF MAJOR BOARDS", j["source_kind"] != "major_board"),
                            ("CLIENT-FACING", a["client_ownership"] == "owns_accounts")] if ok]
    rows.append(dict(job_id=jid, analysis_version="v0.2-draft", model_version="hand-run-reference",
                     title=j["title"], company=j["company"], stratum=j["stratum"], family=j["family"],
                     role_family=j["family"] if j["stratum"] == "title_family" else "free text: " + j["title"],
                     **{k: a[k] for k in ("overlap", "stretch", "stretch_reasons", "wildcard", "ai_relevance", "client_ownership")},
                     why_surfaced=why(j), overlap_points=a["overlap_points"], stretch_points=a["stretch_reasons"],
                     caveats=a["caveats"], worth_opening_because=a["worth_opening_because"],
                     missing_info=missing(j, a), confidence=a["confidence"], workplace_in_text=a["workplace"],
                     suppression=s, feed_tags=tags, source_url=j["source_url"], apply_url=j["final_url"] or j["url"],
                     salary=j["salary"], date_posted=j["date_posted"], desc_len=j["desc_len"], desc_key=desc_key(j)))

with open(os.path.join(HERE, "scouting_analysis.jsonl"), "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps({k: v for k, v in r.items() if k != "desc_key"}, ensure_ascii=False) + "\n")

# Duplicates: same description body under different ids.
groups = collections.defaultdict(list)
for r in rows:
    groups[r["desc_key"]].append(r["job_id"])
dup_groups = [g for g in groups.values() if len(g) > 1]
dup_extra = sum(len(g) - 1 for g in dup_groups)

def interesting(r):
    return r["overlap"] in ("strong", "partial") and not r["suppression"]

metrics = {"n_jobs": len(rows), "duplicate_groups": [[f"{J[i]['company']} | {J[i]['title']}" for i in g] for g in dup_groups],
           "duplicate_extra_rows": dup_extra, "strata": {}, "families": {}}
remote_rows = [r for r in rows if r["family"] != "ALL/any-workplace"]
for s in ("title_family", "description_family", "wildcard"):
    g = [r for r in remote_rows if r["stratum"] == s]
    metrics["strata"][s] = {
        "n": len(g), "overlap": dict(C(r["overlap"] for r in g)), "interesting": sum(interesting(r) for r in g),
        "wildcard_true": sum(r["wildcard"] for r in g), "wildcard_interesting": sum(r["wildcard"] and interesting(r) for r in g),
        "suppressed": sum(bool(r["suppression"]) for r in g), "off_major_boards": sum("OFF MAJOR BOARDS" in r["feed_tags"] for r in g),
        "interesting_off_board": sum(interesting(r) and "OFF MAJOR BOARDS" in r["feed_tags"] for r in g),
        "workplace_in_text": dict(C(r["workplace_in_text"] for r in g)),
        "client_owns_accounts": sum(r["client_ownership"] == "owns_accounts" for r in g)}
for r in remote_rows:
    key = f"{r['stratum']}:{r['family']}"
    m = metrics["families"].setdefault(key, {"n": 0, "strong": 0, "partial": 0, "weak": 0, "very_low": 0, "interesting": 0})
    m["n"] += 1; m[r["overlap"]] += 1; m["interesting"] += interesting(r)
metrics["overall"] = {"interesting": sum(interesting(r) for r in remote_rows), "n": len(remote_rows),
                      "wildcard_interesting": sum(r["wildcard"] and interesting(r) for r in remote_rows),
                      "suppressed": dict(C(r["suppression"]["rule_id"] for r in remote_rows if r["suppression"])),
                      "workplace_in_text": dict(C(r["workplace_in_text"] for r in remote_rows)),
                      "ai_relevance": dict(C(r["ai_relevance"] for r in remote_rows)),
                      "ai_central_interesting": sum(r["ai_relevance"] == "central" and interesting(r) for r in remote_rows)}
json.dump(metrics, open(os.path.join(HERE, "spike_metrics.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(metrics, indent=1, ensure_ascii=False))
