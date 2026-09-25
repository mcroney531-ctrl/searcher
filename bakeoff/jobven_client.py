"""Jobven bakeoff client (one-off, not production ingestion).

Every call is appended to bakeoff/raw/jobven_log.jsonl with its delivered-job
count (len(data), plus X-RateLimit-Remaining before/after as a cross-check), and
every raw response is saved to bakeoff/raw/jobven_<call_id>.json.

Budget is enforced per phase: a call whose worst case (its limit) would push the
phase past its cap is refused. `limit` is ALWAYS passed explicitly, because
omitting it returns the tier maximum (changelog 2026-09-18).
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

API = "https://api.jobven.com"
KEY = os.environ["JOBVEN_API_KEY"]
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
LOG = os.path.join(RAW, "jobven_log.jsonl")

CAPS = {"semantics": 50, "recall": 400, "family": 1500, "reserve": 550}

def spent(phase=None):
    tot = 0
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8"):
            r = json.loads(line)
            if phase is None or r["phase"] == phase:
                tot += r["delivered"]
    return tot

def _get(path, params):
    qs = urllib.parse.urlencode(params, doseq=True)
    url = API + path + ("?" + qs if qs else "")
    req = urllib.request.Request(url, headers={"X-API-Key": KEY, "Accept": "application/json", "User-Agent": "searcher-bakeoff/0.1 (+python)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, dict(r.headers), json.loads(r.read()), url
        except urllib.error.HTTPError as e:
            body = e.read()
            try:
                body = json.loads(body)
            except Exception:
                body = {"raw": body.decode("utf-8", "replace")}
            if e.code == 429 and body.get("error") != "Quota Exceeded":
                time.sleep(float(body.get("retryAfter", 1)) + 0.5)
                continue
            return e.code, dict(e.headers), body, url
    return 429, {}, {"error": "burst retries exhausted"}, url

def call(call_id, phase, params, path="/v1/public/jobs", note="", worst=None):
    """params: list of (k, v) tuples or dict. Returns (status, body)."""
    out = os.path.join(RAW, f"jobven_{call_id}.json")
    if os.path.exists(out):
        d = json.load(open(out, encoding="utf-8"))
        return d["status"], d["response"]
    items = list(params.items()) if isinstance(params, dict) else list(params)
    if path == "/v1/public/jobs" and not any(k == "limit" for k, _ in items):
        raise SystemExit(f"{call_id}: refusing a list call without explicit limit")
    if worst is None:
        worst = int(dict(items).get("limit", 1)) if path == "/v1/public/jobs" else 1
    if spent(phase) + worst > CAPS[phase]:
        print(f"STOP {call_id}: phase {phase} spent {spent(phase)} + worst {worst} > cap {CAPS[phase]}")
        sys.exit(2)
    time.sleep(0.4)  # trial burst cap is 3 req/s
    t0 = time.time()
    status, headers, body, url = _get(path, items)
    h = {k.lower(): v for k, v in headers.items()}
    if path.startswith("/v1/public/companies"):
        delivered = 0  # company lookups are free (pricing FAQ; X-RateLimit-Remaining unchanged)
    elif isinstance(body, dict) and isinstance(body.get("data"), list):
        delivered = len(body["data"])
    elif status == 200 and path != "/v1/public/jobs" and isinstance(body, dict) and body.get("id"):
        delivered = 1
    else:
        delivered = 0
    rec = {"call_id": call_id, "phase": phase, "path": path, "params": items, "status": status,
           "delivered": delivered, "total": (body.get("meta") or {}).get("total") if isinstance(body, dict) else None,
           "has_more": (body.get("meta") or {}).get("hasMore") if isinstance(body, dict) else None,
           "rl_limit": h.get("x-ratelimit-limit"), "rl_remaining": h.get("x-ratelimit-remaining"),
           "seconds": round(time.time() - t0, 2), "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "note": note}
    json.dump({"call_id": call_id, "phase": phase, "url": url, "params": items, "status": status,
               "headers": h, "response": body}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("call_id", "status", "delivered", "total", "has_more", "rl_remaining", "seconds")}))
    return status, body
