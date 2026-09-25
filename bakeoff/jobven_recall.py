"""Phase 2: known-job recall (budget 400). Run: python bakeoff/jobven_recall.py

Per spike job: (0) free company lookup, (A) exact-title q, US, posted since
2026-09-01, any workplace, limit 10; (B) exact title + distinctive description
phrase, active then closed, limit 1. Company names are compared locally.
Writes bakeoff/jobven_recall.json.
"""
import json, os, re, time
from jobven_client import call

HERE = os.path.dirname(os.path.abspath(__file__))
SINCE = 1788220800  # 2026-09-01 00:00 UTC
GLADS = {852046205: 5, 852201874: 7, 851544831: 10, 849294484: 12, 850576240: 14, 851194095: 15, 850645504: 17}

# job_id: (company search tokens, title q, description phrase)
SPEC = {
 852046205: (["Blue Cross", "bcbsnc"], '"Digital Product Analyst"', "maintain a global taxonomy"),
 852201874: (["Citian"], '"Customer Education Specialist"', "Providing training to these individuals"),
 851544831: (["Accenture", "Udacity"], '"AI Learning Operations"', "provide people leadership to"),
 849294484: (["Commerce", "BigCommerce"], '"Technical Training Content Developer"', "and key platform capabilities to"),
 850576240: (["Still University", "atsu"], '"Instructional Designer"', "Help faculty translate learning outcomes"),
 851194095: (["Shipley"], '"Course Developer"', "Maintain ownership of course development"),
 850645504: (["Ladders"], '"Curriculum and Instruction"', "Ensure instructional content aligns with"),
 852195306: (["Khan Academy"], '"Email Marketing"', "We know that transforming education"),
 852185191: (["Solera"], '"Learning and Development Program Manager"', "This role manages the learning"),
 851383703: (["NICE"], '"Education Professional"', "global technical point of contact"),
 852303520: (["Medtronic"], '"Technical Training Specialist"', "Demonstrate training effectiveness through systematic"),
 852286299: (["ZipLiens"], '"Onboarding & Enablement"', "Build the internal enablement curriculum"),
 852099703: (["440 Strategy"], '"Content Manager and Designer"', "and reusable templates using Canva"),
 851275561: (["CVS"], '"Senior Content Designer"', "years experience in UX writing"),
 851058374: (["White Circle"], '"Content Lead"', "content vision and editorial direction"),
 850746530: (["Calculated Hire"], '"SEO Content Strategist"', "Conduct ongoing content audits and"),
 850792055: (["Veeva"], '"Technical Curriculum Developer"', "build the training that teaches"),
 850357921: (["Miaplaza"], '"Music Curriculum Developer"', "Differentiate instruction to accommodate diverse"),
 851123114: (["Edgewater"], '"Training Developer"', "Develop evaluation tools and metrics"),
 849812736: (["Quizcademy"], '"Curriculum Designer"', "into the structured practice students"),
 852327467: (["Lunit"], '"Customer Education"', "Develop a comprehensive education calendar"),
 852034349: (["Arrow Electronics"], '"Content & Enablement Manager"', "end content ecosystem that drives"),
 852260927: (["Spectrio"], '"Director of Customer Education"', "This pivotal position will orchestrate"),
 851631756: (["TalentHop"], '"Senior Customer Education Manager"', "a foundational role in expanding"),
 851873213: (["NYC Health"], '"Instructional Designer"', "The Contact Center Instructional Designer"),
 851964581: (["Spring Health"], '"Clinical Instructional Designer"', "ADDIE model to develop thoughtful"),
 851969875: (["Horizontal"], '"Learning Experience Designer"', "day leadership learning experience for"),
 851079619: (["BJU"], '"Instructional Designer"', "and recordings in the BJUOnline"),
 850873020: (["Wisconsin", "Oshkosh"], '"Learning Technology Specialist"', "Instructional Designer and Learning Technology"),
 850033302: (["AfterQuery"], '"Technical Content Writer"', "own and architect core infrastructure"),
 850608574: (["Mometrix"], '"Technical Writer"', "concise explanations for a learner"),
 852083080: (["Save the Children"], '"Capacity Development"', "global engagement across SCI functions"),
 852248222: (["Pittsburgh"], '"Instructor"', "strong expertise in interprofessional"),
 851470103: (["Crew"], '"AI SDLC Enablement Consultant"', "Upskill product and engineering teams"),
 852286164: (["Fortra"], '"Offensive Security Training Content Developer"', "and maintain practical lab environments"),
}

def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def match(job, tokens, company):
    names = " ".join(norm(c.get("name")) + " " + norm(c.get("website")) for c in job.get("companies", []))
    names += " " + norm(job.get("applyUrl"))
    keys = [norm(t) for t in tokens] + [norm(company)[:10]]
    return any(k and k in names for k in keys)

def main():
    rows = {json.loads(l)["job_id"]: json.loads(l) for l in open(os.path.join(HERE, "scouting_analysis.jsonl"), encoding="utf-8")}
    out = []
    for jid, (tokens, tq, phrase) in SPEC.items():
        r = rows[jid]
        rec = {"job_id": jid, "card": GLADS.get(jid), "company": r["company"], "title": r["title"],
               "stratum": r["stratum"], "ts_date": r["date_posted"], "company_hits": {}, "title_hits": [], "phrase_hits": {}}
        for t in tokens:
            s, b = call(f"rec_{jid}_co_{norm(t)}", "recall", [("search", t), ("limit", 10)], path="/v1/public/companies", note="free company lookup", worst=0)
            rec["company_hits"][t] = [c["name"] for c in (b.get("data") or [])] if s == 200 else f"ERR {s}"
        s, b = call(f"rec_{jid}_title", "recall", [("q", tq), ("country", "US"), ("postedAfter", SINCE), ("limit", 10)], note="exact title, US, since 09-01")
        for j in (b.get("data") or []):
            rec["title_hits"].append({"id": j["id"], "title": j["title"], "company": j["companies"][0]["name"],
                                      "remoteType": j.get("remoteType"), "postedAt": j.get("postedAt"),
                                      "applyUrl": j.get("applyUrl"), "match": match(j, tokens, r["company"])})
        rec["title_more"] = (b.get("meta") or {}).get("hasMore")
        for st in ("active", "closed"):
            s, b = call(f"rec_{jid}_phrase_{st}", "recall", [("q", tq), ("descriptionQuery", phrase), ("status", st), ("postedAfter", SINCE - 60 * 86400), ("limit", 1)],
                        note=f"title + description phrase, {st}")
            rec["phrase_hits"][st] = [{"id": j["id"], "title": j["title"], "company": j["companies"][0]["name"], "postedAt": j.get("postedAt"),
                                       "remoteType": j.get("remoteType"), "applyUrl": j.get("applyUrl"), "status": j.get("status")}
                                      for j in (b.get("data") or [])] if s == 200 else f"ERR {s} {json.dumps(b)[:200]}"
        rec["found"] = any(h["match"] for h in rec["title_hits"]) or any(isinstance(v, list) and v for v in rec["phrase_hits"].values())
        out.append(rec)
        print(f"#{rec['card'] or '-'} {r['company'][:30]:30} found={rec['found']} titlehits={len(rec['title_hits'])} co={rec['company_hits']}")
    json.dump(out, open(os.path.join(HERE, "jobven_recall.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
