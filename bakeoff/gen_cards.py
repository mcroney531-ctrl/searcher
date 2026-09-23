"""Render selected scouting rows as review cards (markdown) plus a CSV for Rone's marks."""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
A = {r["job_id"]: r for r in (json.loads(l) for l in open(os.path.join(HERE, "scouting_analysis.jsonl"), encoding="utf-8"))}

CARDS = [851985369, 852286299, 851383703, 850792055, 852046205, 852083080, 852201874, 851123114, 852286164,
         851544831, 851470103, 849294484, 852034349, 850576240, 851194095, 852195306, 850645504, 850033302,
         851058374, 850274105]

def src(u):
    if not u:
        return "?"
    h = u.split("/")[2].replace("www.", "")
    return h

out = []
for n, jid in enumerate(CARDS, 1):
    r = A[jid]
    tags = " · ".join(r["feed_tags"]) or "no tags"
    head = f"### {n}. {r['title']} at {r['company']}"
    if r["suppression"]:
        head += " (FILTERED: " + r["suppression"]["evidence"] + ")"
    out.append(head)
    out.append(f"`{tags}` · overlap **{r['overlap']}** · stretch **{r['stretch']}** · AI {r['ai_relevance']} · "
               f"{r['salary'] or 'salary not stated'} · posted {r['date_posted']}")
    out.append(f"- **Why surfaced:** {r['why_surfaced']}")
    out.append(f"- **Overlap:** {'; '.join(r['overlap_points']) or 'none'}")
    if r["stretch_points"]:
        out.append(f"- **Stretch:** {'; '.join(r['stretch_points'])}")
    if r["caveats"]:
        out.append(f"- **Caveats:** {'; '.join(r['caveats'])}")
    out.append(f"- **Worth opening because:** {r['worth_opening_because']}")
    if r["missing_info"]:
        out.append(f"- **Missing:** {', '.join(r['missing_info'])}")
    out.append(f"- **Seen via:** {src(r['source_url'])} · **Apply:** {r['apply_url']}")
    out.append(f"- [ ] Glad I saw this  ·  [ ] Already found it myself  ·  confidence {r['confidence']}")
    out.append("")
open(os.path.join(HERE, "spike_cards.md"), "w", encoding="utf-8").write("\n".join(out))

with open(os.path.join(HERE, "spike_cards_marks.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["card", "job_id", "company", "title", "stratum", "overlap", "wildcard", "off_major_boards",
                "glad_i_saw_this", "already_found_myself", "notes"])
    for n, jid in enumerate(CARDS, 1):
        r = A[jid]
        w.writerow([n, jid, r["company"], r["title"], r["stratum"], r["overlap"], r["wildcard"],
                    "OFF MAJOR BOARDS" in r["feed_tags"], "", "", ""])
print("\n".join(out))
