#!/usr/bin/env python3
"""Bull Desk shared state cache.

The one process on the desk allowed to call Webull's account read endpoints
(balance, positions, open orders), which are limited to 2 requests per 2
seconds each. Writes JSON snapshots under /workspace/trading-desk/state/ for
every Bot to read. A file lock collapses concurrent callers; a minimum age
stops refresh storms.

Usage:
  bd_state.py refresh --account-id <id> [--min-age 10]
  bd_state.py age
  bd_state.py events --account-id <id>     # trade-events subscriber (best effort)

Requires: webull-skill on PATH (see skills/webull-setup), configured via the
desk .env. Read-only: this script never places, replaces or cancels anything.
"""
import argparse, datetime, fcntl, json, os, pathlib, subprocess, sys, time

STATE = pathlib.Path(os.environ.get("BULL_DESK_STATE", "/workspace/trading-desk/state"))
SNAPSHOTS = {           # name -> webull-skill trading action
    "balance": "balance",
    "positions": "position",
    "open_orders": "open",
}

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run_cli(action, account_id):
    cmd = ["webull-skill", "trading", "--action", action, "--account-id", account_id]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                       cwd="/workspace/trading-desk")
    return p.returncode, p.stdout, p.stderr

def refresh(account_id, min_age):
    STATE.mkdir(parents=True, exist_ok=True)
    lock_path = STATE / ".lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)          # concurrent Bots queue here
        wrote, skipped = [], []
        for name, action in SNAPSHOTS.items():
            out_path = STATE / f"{name}.json"
            if out_path.exists() and time.time() - out_path.stat().st_mtime < min_age:
                skipped.append(name)
                continue
            code, out, err = run_cli(action, account_id)
            snap = {
                "fetched_at_utc": utcnow(),
                "environment": os.environ.get("WEBULL_ENVIRONMENT", "uat"),
                "account_id": account_id,
                "action": action,
                "ok": code == 0,
                "output": out.strip() if code == 0 else "",
                "error": err.strip() if code != 0 else "",
            }
            tmp = out_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(snap, indent=2))
            tmp.replace(out_path)
            wrote.append(name if code == 0 else f"{name}(ERROR)")
            time.sleep(1.2)                        # stay far inside 2 req / 2 s
        print(f"refreshed: {', '.join(wrote) or 'nothing'}"
              + (f"; fresh enough (<{min_age}s): {', '.join(skipped)}" if skipped else ""))

def age():
    if not STATE.exists():
        print("no state directory yet - run refresh first"); return
    now = time.time()
    for name in SNAPSHOTS:
        p = STATE / f"{name}.json"
        print(f"{name}: {int(now - p.stat().st_mtime)}s old" if p.exists() else f"{name}: missing")

def events(account_id):
    """Best-effort gRPC trade-events subscriber. The SDK API surface varies by
    version; if unavailable, exit 3 so the desk knows to rely on detail polling
    (which is the source of truth regardless - see skills/webull-streaming)."""
    hb = STATE / "events.heartbeat"
    STATE.mkdir(parents=True, exist_ok=True)
    try:
        from webullsdktradeeventscore.events_client import EventsClient  # official SDK
    except Exception:
        print("trade-events subscriber unavailable in this SDK install; "
              "relying on detail polling (that is the truth anyway)", file=sys.stderr)
        sys.exit(3)
    app_key, app_secret = os.environ.get("WEBULL_APP_KEY"), os.environ.get("WEBULL_APP_SECRET")
    if not (app_key and app_secret):
        print("no credentials in environment", file=sys.stderr); sys.exit(2)
    region = os.environ.get("WEBULL_REGION_ID", "us")
    client = EventsClient(app_key, app_secret, region_id=region)
    def on_event(event_type, subscribe_type, payload, raw=None):
        line = {"received_at_utc": utcnow(), "event_type": str(event_type), "payload": str(payload)}
        print(json.dumps(line), flush=True)
        hb.touch()
    client.on_events_message = on_event
    print(f"subscribing to trade events for account {account_id} ({region})", flush=True)
    hb.touch()
    client.do_subscribe([account_id])              # blocks; supervise externally

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("refresh"); r.add_argument("--account-id", required=True); r.add_argument("--min-age", type=float, default=10.0)
    sub.add_parser("age")
    e = sub.add_parser("events"); e.add_argument("--account-id", required=True)
    a = ap.parse_args()
    if a.cmd == "refresh": refresh(a.account_id, a.min_age)
    elif a.cmd == "age": age()
    else: events(a.account_id)
