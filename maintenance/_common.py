"""R2D2 maintenance — shared helpers.
READ-ONLY against trading data. Fabric writes only for R2D2 audit results.
UTC discipline absolute. No NOW()/utcnow()/time.time().
Methodology: r2d2:methodology:maintenance:v1
Main directive: r2d2:directive:main (preservation of the team)."""
import json, urllib.request, urllib.parse, subprocess, sys, datetime
from pathlib import Path

FABRIC = "http://localhost:8080/api/v1/redis"
SSH_TARGET = "root@192.168.11.10"
DB_HOST_PORT = "127.0.0.1:3307"
DISCORD_BRIDGE = "/srv/team_discord"
PERSONA = "R2D2"


def fabric_get(key):
    try:
        r = urllib.request.urlopen(f"{FABRIC}/get/{urllib.parse.quote(key, safe=':')}", timeout=10)
        d = json.loads(r.read())
        v = d.get("value")
        if v is None: return None
        try: return json.loads(v)
        except: return v
    except Exception as e:
        return None


def fabric_set(key, value):
    body = json.dumps({"key": key, "value": json.dumps(value) if not isinstance(value, str) else value}).encode()
    req = urllib.request.Request(f"{FABRIC}/set", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10).read()
        return True
    except Exception as e:
        print(f"FABRIC_SET_FAIL {key}: {e}", file=sys.stderr)
        return False


def remote_query(sql, db="tradingScalp"):
    """Run a MySQL query on dell-debian via SSH. Returns parsed rows (list of dicts)."""
    # Use mysql with -B (batch) and parse tab-separated output
    cmd = ["ssh", SSH_TARGET,
           f"mysql -h127.0.0.1 -P3307 -uroot -pPDAPass@R00t123 {db} -B -e \"{sql.replace('\"', '\\\"')}\""]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            print(f"REMOTE_QUERY_FAIL: {out.stderr[:300]}", file=sys.stderr)
            return None
        lines = out.stdout.strip().split("\n")
        if not lines or len(lines) < 1: return []
        headers = lines[0].split("\t")
        rows = []
        for line in lines[1:]:
            cells = line.split("\t")
            row = {h: (c if c != "NULL" else None) for h, c in zip(headers, cells)}
            rows.append(row)
        return rows
    except Exception as e:
        print(f"REMOTE_QUERY_EXC: {e}", file=sys.stderr)
        return None


def canonical_now_utc():
    """Get UTC anchor from MAX(timestamp) in helios_strategy_signals. Fail loud if missing."""
    rows = remote_query("SELECT MAX(timestamp) AS now FROM helios_strategy_signals")
    if not rows or not rows[0].get("now"):
        print("FAIL_LOUD: cannot derive canonical_now_utc from data", file=sys.stderr)
        sys.exit(2)
    raw = rows[0]["now"]
    return datetime.datetime.fromisoformat(raw.replace(" ", "T")).replace(tzinfo=datetime.timezone.utc)


def discord_post(text, priority="normal", topic=None, force=False):
    """Post to #the-rogue-alliance with rate-limiting per topic.
    By default, allows max 1 post per topic per UTC day.
    Set force=True to bypass rate limit (use sparingly).
    Returns True if posted, False if rate-limited or error."""
    if topic and not force:
        anchor = canonical_now_utc()
        date_str = anchor.strftime("%Y%m%d")
        rate_key = f"r2d2:rate_limit:discord:{topic}:{date_str}"
        existing = fabric_get(rate_key)
        if existing:
            print(f"DISCORD_RATE_LIMITED: topic={topic} date={date_str}", file=sys.stderr)
            return False
    try:
        sys.path.insert(0, DISCORD_BRIDGE)
        from client import post_to_team
        post_to_team(PERSONA, text, priority=priority)
        if topic:
            fabric_set(rate_key, {"posted_utc": canonical_now_utc().isoformat(), "priority": priority})
        return True
    except Exception as e:
        print(f"DISCORD_POST_FAIL: {e}", file=sys.stderr)
        return False


def log_run(script_name, status, summary):
    """Log a run summary to fabric for cross-session visibility."""
    anchor = canonical_now_utc()
    key = f"r2d2:maintenance:run:{script_name}:latest"
    fabric_set(key, {
        "script": script_name,
        "ran_utc": anchor.isoformat(),
        "status": status,
        "summary": summary
    })
