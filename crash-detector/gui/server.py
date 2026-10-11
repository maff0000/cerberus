"""CERBERUS WO-1.4 — a plain, honest DEV GUI over the ingestion store (stdlib only).

    GET /            the page: two dials side by side (never blended) + every indicator's state
    GET /api/state   the same view-model as JSON
    GET /healthz     200 with the build fingerprint if the store is readable, 503 otherwise

Read-only: the store is opened ``mode=ro`` and nothing here writes. Configuration comes from the
environment: ``CD_DB_PATH`` (required), ``CD_BIND_HOST`` / ``CD_BIND_PORT``, ``CD_BUILD_SHA``.

This is not polish. The bar is: the two dials never blended, an absent dial says NO READING and
why, and every indicator shows its value, LIVE/PENDING-and-why, and its age.
"""

from __future__ import annotations

import html
import json
import os
import signal
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gui.state import build_state
from ingestion.store import SqliteStore

BUILD_SHA = os.environ.get("CD_BUILD_SHA", "unknown")
REFRESH_SECONDS = 60

CSS = """
body{font:15px/1.45 system-ui,sans-serif;margin:0;background:#f4f5f7;color:#1c2330}
header{background:#1c2330;color:#fff;padding:14px 24px}
header h1{margin:0;font-size:20px} header small{color:#aab3c5}
.banner{background:#fff3cd;border-bottom:2px solid #e0b100;padding:10px 24px;font-weight:600}
main{padding:20px 24px;max-width:1280px}
.dials{display:flex;gap:20px;flex-wrap:wrap}
.dial{flex:1 1 380px;background:#fff;border:1px solid #cfd5df;border-radius:6px;padding:16px 20px}
.dial h2{margin:0 0 6px;font-size:16px;text-transform:uppercase;letter-spacing:.05em;color:#46506a}
.num{font-size:52px;font-weight:700;line-height:1.1}
.num.none{font-size:30px;color:#8a1c1c}
.tag{display:inline-block;padding:2px 8px;border-radius:3px;font-size:12px;font-weight:700;color:#fff}
.VALUE,.LIVE{background:#1f7a3d}.DEGRADED,.STALE,.PARTIAL{background:#b26a00}
.NOREADING,.MISSING,.FEED_FAILING{background:#a61e1e}.PENDING,.DERIVED,.NOT_TRACTABLE{background:#5b6479}
.why{color:#46506a;font-size:13px;margin-top:6px}
table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #cfd5df;margin-top:6px}
th,td{padding:5px 8px;border-bottom:1px solid #e4e8ef;text-align:left;vertical-align:top;font-size:13px}
th{background:#e9edf3;position:sticky;top:0}
td.n{text-align:right;font-variant-numeric:tabular-nums}
h3{margin:26px 0 4px} footer{padding:16px 24px;color:#6a7488;font-size:12px}
"""


def _tag(status: str) -> str:
    return f'<span class="tag {html.escape(status.replace(" ", ""))}">{html.escape(status)}</span>'


def _dial_html(d: dict) -> str:
    esc = html.escape
    if d["value"] is None:
        number = '<div class="num none">NO READING</div>'
    else:
        number = f'<div class="num">{d["value"]:.3f}</div><div class="why">scale 0–1, placeholder bands, higher = more stress</div>'
    lines = [f'<h2>{esc(d["title"])}</h2>', _tag(d["status"]), number]
    if d["as_of_utc"]:
        lines.append(f'<div class="why">oldest scored input as of {esc(d["as_of_utc"])}</div>')
    if d["reason"]:
        lines.append(f'<div class="why"><b>Why:</b> {esc(d["reason"])}</div>')
    if d["missing_inputs"]:
        lines.append(f'<div class="why"><b>Missing / stale inputs:</b> {esc(", ".join(d["missing_inputs"]))}</div>')
    cov = d["coverage"]
    lines.append(
        f'<div class="why"><b>Coverage:</b> {cov["fraction"]:.0%} of this dial\'s ratified indicator weight is wired. '
        f'Still PENDING (not in this number): {esc(", ".join(cov["pending"]))}</div>'
    )
    if d["inputs_used"]:
        lines.append(f'<div class="why">Inputs used: {esc(", ".join(d["inputs_used"]))}</div>')
    return '<section class="dial">' + "".join(lines) + "</section>"


def _fmt(value: object, unit: str) -> str:
    if value is None:
        return "—"
    return f"{value:,.4g}".replace("e+", "e") + (f" {unit}" if unit else "")


def _row_html(e: dict) -> str:
    esc = html.escape
    dials = ", ".join(e["dials"]) if e["dials"] else "—"
    asof = esc(e["as_of_utc"][:10]) if e["as_of_utc"] else "—"
    age = f'{e["age_days"]}d' if e["age_days"] is not None else "—"
    return (
        f'<tr><td>{esc(e["id"])}</td><td>{esc(e["name"])}</td><td>{e["tier"]}</td>'
        f'<td>{esc(dials)}</td><td>{_tag(e["state"])}</td>'
        f'<td class="n">{esc(_fmt(e["value"], e["unit"]))}</td><td>{asof}</td>'
        f'<td class="n">{age} / {e["window_days"]}d</td><td>{esc(e["why"])}</td></tr>'
    )


def render_page(state: dict) -> str:
    esc = html.escape
    counts = ", ".join(f"{esc(k)}: {v}" for k, v in sorted(state["counts"].items()))
    order = {"LIVE": 0, "STALE": 1, "FEED_FAILING": 1, "MISSING": 1}
    rows = sorted(state["indicators"], key=lambda e: (order.get(e["state"], 2), e["id"]))
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta http-equiv="refresh" content="{REFRESH_SECONDS}">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>CERBERUS — crash detector (DEV)</title><style>{CSS}</style></head><body>'
        '<header><h1>CERBERUS — crash detector <small>DEV live view · advisory only</small></h1></header>'
        f'<div class="banner">{esc(state["provisional"])}</div><main>'
        '<div class="dials">' + "".join(_dial_html(d) for d in state["dials"]) + "</div>"
        "<p class=\"why\">The two dials are separate quantities and are never combined. "
        "A dial with missing or stale required inputs shows NO READING, never a calm number.</p>"
        f"<h3>Indicators ({esc(counts)})</h3>"
        "<table><thead><tr><th>id</th><th>name</th><th>tier</th><th>scored in dial</th><th>state</th>"
        "<th>value</th><th>as of</th><th>age / window</th><th>why not live / detail</th></tr></thead><tbody>"
        + "".join(_row_html(e) for e in rows)
        + f"</tbody></table></main><footer>generated {esc(state['generated_utc'])} · build "
        f"<code>{esc(BUILD_SHA)}</code> · refreshes every {REFRESH_SECONDS}s</footer></body></html>"
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "cd-gui"

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-CD-Build", BUILD_SHA)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (stdlib name)
        path = self.path.split("?", 1)[0]
        if path not in ("/", "/api/state", "/healthz"):
            self._send(404, b"not found\n", "text/plain; charset=utf-8")
            return
        try:
            with SqliteStore(self.server.db_path, read_only=True) as store:  # type: ignore[attr-defined]
                state = build_state(store, datetime.now(timezone.utc))
        except Exception as failure:  # an unreadable store is a refusal to render, never a calm page
            self._send(503, f"store unreadable: {type(failure).__name__}\n".encode(), "text/plain; charset=utf-8")
            sys.stderr.write(f"state build failed: {type(failure).__name__}: {failure}\n")
            return
        if path == "/healthz":
            self._send(200, json.dumps({"ok": True, "build": BUILD_SHA}).encode(), "application/json")
        elif path == "/api/state":
            self._send(200, json.dumps(state, indent=1).encode(), "application/json")
        else:
            self._send(200, render_page(state).encode(), "text/html; charset=utf-8")

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    db_path = os.environ.get("CD_DB_PATH")
    if not db_path:
        raise SystemExit("REFUSED: CD_DB_PATH is unset.")
    host = os.environ.get("CD_BIND_HOST", "127.0.0.1")
    port = int(os.environ.get("CD_BIND_PORT", "8710"))
    server = ThreadingHTTPServer((host, port), Handler)
    server.db_path = db_path  # type: ignore[attr-defined]
    print(f"cd-gui build={BUILD_SHA} listening on {host}:{port} db={db_path}", flush=True)
    # PID 1 in a container ignores SIGTERM unless a handler is installed; shutdown() must run off-thread.
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
