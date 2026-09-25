"""Phase 3: family replay (budget 1500). US + remoteType=remote + posted in the last 7 days.

Title families: one q per family (OR of quoted titles), paged to completion.
Description phrases: one call per phrase (descriptionQuery takes one phrase; no OR),
with title exclusions as q -"phrase" terms (q is capped at 200 chars, so only the
highest-volume TITLE_EXCLUDE terms fit; the full regex list is applied locally after).
Sizing-only extras (limit 1 + includeTotal): each phrase without exclusions, and
remote+flexible volume per family/phrase.
Writes bakeoff/jobven_family_jobs.jsonl (one row per delivery) and jobven_family_sizes.json.
"""
import json, os, re, time
from jobven_client import call, spent
os.environ.setdefault("THEIRSTACK_API_KEY", "unused")  # theirstack_spike reads it at import; no calls are made
from theirstack_spike import TITLE_FAMILIES, TITLE_EXCLUDE

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_AT = 1790307000  # fixed so reruns reuse cached raw files (2026-09-25 ~03:30 UTC)
T7 = RUN_AT - 7 * 86400
US_REMOTE = [("country", "US"), ("remoteType[]", "remote")]
US_REMOTE_FLEX = [("country", "US"), ("remoteType[]", "remote"), ("remoteType[]", "flexible")]

# TheirStack regex variants expanded to literal phrases (descriptionQuery is literal whole-word).
DESC_PHRASES = {
    "course_content": ["develop course content", "developing course content", "course development", "learning content", "e-learning content"],
    "curriculum": ["curriculum development", "design curriculum", "designing curriculum", "design the curriculum", "designing the curriculum", "training curriculum"],
    "enablement_material": ["enablement materials", "enablement content", "playbooks and training"],
    "customer_training": ["customer training", "customer education", "onboarding content", "academy content"],
    "knowledge_content": ["knowledge base", "help center content", "content operations", "content governance"],
    "ai_adoption": ["AI adoption", "AI literacy", "AI training program", "teach teams to use AI"],
}
EXCL_Q_TERMS = ["account executive", "account manager", "sales representative", "sales manager",
                "customer service representative", "help desk", "customer success manager", "support specialist"]
EXCL_Q = " ".join(f'-"{t}"' for t in EXCL_Q_TERMS)
assert len(EXCL_Q) <= 200, len(EXCL_Q)

def slug(s):
    return re.sub(r"\W+", "_", s).strip("_").lower()

def pull(prefix, params, rows, mode, family, phrase=None):
    cursor, page = None, 0
    while True:
        p = list(params) + [("limit", 25)] + ([("cursor", cursor)] if cursor else [])
        s, b = call(f"{prefix}_p{page}", "family", p, note=f"{mode} {family} {phrase or ''}".strip())
        if s != 200:
            print("ERR", prefix, json.dumps(b)[:300]); return
        for j in b["data"]:
            rows.append({"mode": mode, "family": family, "phrase": phrase, "call": f"{prefix}_p{page}", "job": j})
        cursor = b["meta"].get("nextCursor")
        if not b["meta"].get("hasMore") or not cursor:
            return
        page += 1

def size(cid, params, note):
    s, b = call(cid, "family", list(params) + [("limit", 1), ("includeTotal", "true")], note=note)
    return (b.get("meta") or {}).get("total") if s == 200 else f"ERR {s}"

def main():
    rows, sizes = [], {"title": {}, "desc": {}}
    for fam, (titles, _must) in TITLE_FAMILIES.items():
        q = " OR ".join(f'"{t}"' for t in titles)
        pull(f"fam_title_{fam}", [("q", q), *US_REMOTE, ("postedAfter", T7)], rows, "title_family", fam)
        sizes["title"][fam] = {"remote": sum(1 for r in rows if r["family"] == fam and r["mode"] == "title_family"),
                               "remote_flex": size(f"fam_size_title_{fam}_flex", [("q", q), *US_REMOTE_FLEX, ("postedAfter", T7)], "sizing remote+flexible")}
    for fam, phrases in DESC_PHRASES.items():
        for ph in phrases:
            before = len(rows)
            pull(f"fam_desc_{slug(ph)}", [("q", EXCL_Q), ("descriptionQuery", ph), *US_REMOTE, ("postedAfter", T7)], rows, "description_family", fam, ph)
            sizes["desc"][ph] = {"family": fam, "remote_excl": len(rows) - before,
                                 "remote_noexcl": size(f"fam_size_desc_{slug(ph)}_noexcl", [("descriptionQuery", ph), *US_REMOTE, ("postedAfter", T7)], "sizing without exclusions"),
                                 "remote_flex_excl": size(f"fam_size_desc_{slug(ph)}_flex", [("q", EXCL_Q), ("descriptionQuery", ph), *US_REMOTE_FLEX, ("postedAfter", T7)], "sizing remote+flexible")}
            print(ph, sizes["desc"][ph])
    with open(os.path.join(HERE, "jobven_family_jobs.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(sizes, open(os.path.join(HERE, "jobven_family_sizes.json"), "w", encoding="utf-8"), indent=1)
    print("family spent", spent("family"), "rows", len(rows), "unique", len({r["job"]["id"] for r in rows}))

if __name__ == "__main__":
    main()
