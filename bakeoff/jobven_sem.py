"""Phase 1: API semantics probes (budget 50). Run: python bakeoff/jobven_sem.py <step>"""
import json, sys, time
from jobven_client import call

T7 = int(time.time()) - 7 * 86400
US = [("country", "US"), ("remoteType[]", "remote")]
NONS = ("q", "zzqxvwj")  # nonsense title term: guarantees 0 results so probes are free

def step1():
    s, b = call("sem_02_baseline_id", "semantics",
                [("q", '"instructional designer"'), *US, ("postedAfter", T7), ("limit", 1),
                 ("includeTotal", "true"), ("descriptionFormat", "all")],
                note="baseline: 1 job with all description formats + total")
    j = b["data"][0]
    print(json.dumps({k: (v if k not in ("description", "descriptionPlain", "descriptionMarkdown") else len(v or "")) for k, v in j.items()}, indent=1)[:3000])
    print("META", b["meta"])

def probes():
    # Unknown params: 400 = rejected, 200-empty = accepted. Always free.
    tests = {
        "sem_p_limit0_total": [NONS, ("limit", 0), ("includeTotal", "true")],
        "sem_p_companyIds": [NONS, ("companyIds[]", "x"), ("limit", 1)],
        "sem_p_excludeIds": [NONS, ("excludeIds[]", "00000000-0000-0000-0000-000000000000"), ("limit", 1)],
        "sem_p_excludeIds_plain": [NONS, ("excludeIds", "00000000-0000-0000-0000-000000000000"), ("limit", 1)],
        "sem_p_idNot": [NONS, ("idNot[]", "00000000-0000-0000-0000-000000000000"), ("limit", 1)],
        "sem_p_exclude": [NONS, ("exclude[]", "00000000-0000-0000-0000-000000000000"), ("limit", 1)],
        "sem_p_ids": [NONS, ("ids[]", "00000000-0000-0000-0000-000000000000"), ("limit", 1)],
        "sem_p_createdAfter": [NONS, ("createdAfter", T7), ("limit", 1)],
        "sem_p_updatedAfter": [NONS, ("updatedAfter", T7), ("limit", 1)],
        "sem_p_indexedAfter": [NONS, ("indexedAfter", T7), ("limit", 1)],
        "sem_p_firstSeenAfter": [NONS, ("firstSeenAfter", T7), ("limit", 1)],
        "sem_p_discoveredAfter": [NONS, ("discoveredAfter", T7), ("limit", 1)],
        "sem_p_since": [NONS, ("since", T7), ("limit", 1)],
        "sem_p_sort_createdAt": [NONS, ("sortBy", "createdAt"), ("limit", 1)],
        "sem_p_sort_updatedAt": [NONS, ("sortBy", "updatedAt"), ("limit", 1)],
        "sem_p_sort_firstSeenAt": [NONS, ("sortBy", "firstSeenAt"), ("limit", 1)],
        "sem_p_sort_company": [NONS, ("sortBy", "company"), ("limit", 1)],
        "sem_p_descq_repeat": [NONS, ("descriptionQuery", "course development"), ("descriptionQuery", "curriculum development"), ("postedAfter", T7), ("limit", 1)],
        "sem_p_descq_bracket": [NONS, ("descriptionQuery[]", "course development"), ("descriptionQuery[]", "curriculum development"), ("postedAfter", T7), ("limit", 1)],
        "sem_p_q_only_exclusion": [("q", '-"account executive"'), ("descriptionQuery", "zzqxvwj qqq"), ("postedAfter", T7), ("limit", 1)],
    }
    for cid, p in tests.items():
        s, b = call(cid, "semantics", p, note="param probe (nonsense q => free)", worst=0)
        print("   ", cid, s, json.dumps(b)[:260])


def paid():
    F = [*US, ("postedAfter", T7)]
    L = [("limit", 1), ("includeTotal", "true")]
    tests = [
        ("sem_03_q_id_unquoted", [("q", "instructional designer"), *F, *L], "unquoted title words"),
        ("sem_04_q_id_anywhere", [("q", '"instructional designer"'), ("postedAfter", T7), *L], "no country/remote filter"),
        ("sem_05_q_id_us_anywork", [("q", '"instructional designer"'), ("country", "US"), ("postedAfter", T7), *L], "US, any workplace"),
        ("sem_06_q_title_plus_descword", [("q", '"Lead Instructional Designer" Skilljar'), *F, *L], "Skilljar only in Neon One description: 0 => q is title-only"),
        ("sem_07_q_descword_alone", [("q", "Skilljar"), *F, *L], "desc-only word in q"),
        ("sem_08_descq_confirms", [("q", '"Lead Instructional Designer"'), ("descriptionQuery", "Skilljar"), *F, *L], "same word via descriptionQuery => expect 1"),
        ("sem_09_descq_A", [("descriptionQuery", "curriculum development"), *F, *L], "phrase A"),
        ("sem_10_descq_B", [("descriptionQuery", "course development"), *F, *L], "phrase B"),
        ("sem_11_descq_A_OR_B", [("descriptionQuery", "curriculum development OR course development"), *F, *L], "OR inside descriptionQuery"),
        ("sem_12_descq_quoted_pair", [("descriptionQuery", '"curriculum development" "course development"'), *F, *L], "two quoted phrases"),
        ("sem_13_q_OR_phrases", [("q", '"instructional designer" OR "curriculum developer" OR "learning designer"'), *F, *L], "q OR of phrases"),
        ("sem_14_q_cd", [("q", '"curriculum developer"'), *F, *L], "component"),
        ("sem_15_q_ld", [("q", '"learning designer"'), *F, *L], "component"),
        ("sem_16_all_us_remote_7d", [*F, *L], "index size: all US remote, 7d (webhook job.created proxy)"),
        ("sem_17_all_us_7d", [("country", "US"), ("postedAfter", T7), *L], "all US any workplace 7d"),
        ("sem_18_all_7d", [("postedAfter", T7), *L], "everything 7d"),
        ("sem_19_all_active", [*L], "everything active, no date"),
        ("sem_20_descq_kb", [("descriptionQuery", "knowledge base"), *F, *L], "exclusion baseline"),
        ("sem_21_descq_kb_excl", [("descriptionQuery", "knowledge base"), ("q", '-"account executive" -"help desk" -"customer support"'), *F, *L], "q phrase exclusions with descriptionQuery"),
    ]
    for cid, p, note in tests:
        s, b = call(cid, "semantics", p, note=note)
        if s != 200:
            print("   ERR", cid, json.dumps(b)[:300])
        elif b["data"]:
            j = b["data"][0]
            print("   ->", j["title"], "|", j["companies"][0]["name"], "|", j.get("remoteType"), "| total", b["meta"].get("total"))

def companies():
    from jobven_client import call as c
    for cid, p in [("sem_c1_search_neon", [("search", "Neon One"), ("limit", 5)]),
                   ("sem_c2_sort_active", [("sortBy", "activeJobsCount"), ("sortOrder", "DESC"), ("limit", 5)])]:
        s, b = c(cid, "semantics", p, path="/v1/public/companies", note="company lookup (free)", worst=0)
        print(cid, s, json.dumps(b)[:1200])

if __name__ == "__main__":
    globals()[sys.argv[1]]()
