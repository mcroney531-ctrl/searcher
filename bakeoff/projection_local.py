"""Free, local checks for docs/credit-projection.md (no API calls).
1. Which sampled jobs each title exclusion would remove (must spare all glads and interesting jobs).
2. Re-match every sampled description against every description phrase: which glads/interesting
   jobs each phrase catches, and which jobs depend on a single phrase."""
import csv, json, os, re, collections
from theirstack_spike import TITLE_EXCLUDE, DESC_FAMILIES, TITLE_FAMILIES

HERE = os.path.dirname(os.path.abspath(__file__))
J = {j["id"]: j for j in (json.loads(l) for l in open(os.path.join(HERE, "jobs_sample.jsonl"), encoding="utf-8"))}
A = {r["job_id"]: r for r in (json.loads(l) for l in open(os.path.join(HERE, "scouting_analysis.jsonl"), encoding="utf-8"))}
marks = list(csv.DictReader(open(os.path.join(HERE, "spike_cards_marks.csv"), encoding="utf-8")))
GLAD = {int(m["job_id"]): int(m["card"]) for m in marks if m["glad_i_saw_this"].strip().lower() == "yes"}

def interesting(r):
    return r["overlap"] in ("strong", "partial") and not r["suppression"]

def label(jid):
    r = A[jid]
    tag = f"GLAD #{GLAD[jid]}" if jid in GLAD else ("interesting" if interesting(r) else r["overlap"])
    return f"{J[jid]['title'][:60]} @ {J[jid]['company']} [{tag}]"

out = {"glads": {str(k): v for k, v in GLAD.items()}, "title_exclude": {}, "phrases": {}}

print("== title exclusions on the 144 sampled jobs ==")
removed_total = set()
for term, pat in TITLE_EXCLUDE.items():
    hits = [jid for jid in J if re.search(pat, J[jid]["title"])]
    removed_total |= set(hits)
    bad = [jid for jid in hits if jid in GLAD or interesting(A[jid])]
    out["title_exclude"][term] = {"removes": len(hits), "removes_glad_or_interesting": [label(j) for j in bad],
                                  "examples": [label(j) for j in hits[:4]]}
    print(f"{term:16} removes {len(hits):2}  bad={len(bad)}  e.g. {[J[j]['title'][:40] for j in hits[:3]]}")
bad_total = [j for j in removed_total if j in GLAD or interesting(A[j])]
by_overlap = collections.Counter(A[j]["overlap"] for j in removed_total)
out["title_exclude_total"] = {"removed": len(removed_total), "by_overlap": dict(by_overlap),
                              "glad_or_interesting_removed": [label(j) for j in bad_total]}
print("total removed:", len(removed_total), dict(by_overlap), "glad/interesting removed:", [label(j) for j in bad_total])

# Non-obvious titles that sit close to the exclusion list: make sure nothing content-ish is caught.
for probe in ["Customer Success Content & Enablement Manager", "Sales Enablement Content Manager", "Customer Education Specialist",
              "Senior Digital Product Analyst", "Business Development Course Developer", "Technical Support Content Writer",
              "Customer Service Training Specialist", "Sales Enablement Manager", "Account Management Training Lead"]:
    hit = [t for t, p in TITLE_EXCLUDE.items() if re.search(p, probe)]
    print(f"probe {probe!r}: {'EXCLUDED by ' + ','.join(hit) if hit else 'kept'}")
    out.setdefault("probes", {})[probe] = hit

print("\n== description phrases re-matched against all 144 sampled descriptions ==")
phrase_hits = {}
for fam, ps in DESC_FAMILIES.items():
    for p in ps:
        hits = {jid for jid in J if re.search("(?i)" + p, J[jid]["description"])}
        phrase_hits[p] = hits
        g = sorted(GLAD[j] for j in hits if j in GLAD)
        ints = [j for j in hits if interesting(A[j])]
        out["phrases"][p] = {"family": fam, "sample_matches": len(hits), "glads": g, "interesting": len(ints),
                             "interesting_titles": [label(j) for j in ints]}
        print(f"{fam:20} {p:32} matches {len(hits):3}  glads {g}  interesting {len(ints)}")

# Jobs (interesting or glad) that only one phrase catches, and are not reachable by title families.
def title_hit(t):
    return any(all(w in t.lower() for w in title.lower().split()) for ts, _ in TITLE_FAMILIES.values() for title in ts)
print("\n== interesting/glad jobs reachable ONLY by description, and which phrases catch them ==")
only = {}
for jid in J:
    if not (interesting(A[jid]) or jid in GLAD) or title_hit(J[jid]["title"]):
        continue
    ps = [p for p, h in phrase_hits.items() if jid in h]
    only[label(jid)] = ps
    print(f"{label(jid)}  <- {ps}")
out["description_only_finds"] = only
json.dump(out, open(os.path.join(HERE, "projection_local.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
