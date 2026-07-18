import json
import os
import re
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=None)

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / "state.json"

# Set this as a secret environment variable on your host.
ADMIN_KEY = os.environ.get("ADMIN_KEY", "change-me")
LOCK = threading.RLock()
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_STATE = {
    "duration_seconds": 86400,
    "remaining_seconds": 86400,
    "running": False,
    "end_time": None,
    "title": "24 HOURS OF CHAOS",
    "subtitle": "LIVE WITH",
    "host_name": "YOUR NAME",
    "primary_color": "#f1f1ed",
    "secondary_color": "#c42d2d",
    "text_color": "#f7f7f2",
    "portal_speed": 1.0,
    "glow_strength": 0.75,
    "show_milliseconds": False,
    "timer_only": False,
    "updated_at": time.time(),
}


def load_state():
    if STATE_FILE.exists():
        try:
            saved = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            state = DEFAULT_STATE.copy()
            state.update(saved)
            return state
        except (OSError, ValueError, TypeError):
            pass
    return DEFAULT_STATE.copy()


STATE = load_state()


def save_state():
    STATE["updated_at"] = time.time()
    temp = STATE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(STATE, indent=2), encoding="utf-8")
    temp.replace(STATE_FILE)


def materialize_remaining(now=None):
    now = now or time.time()
    if STATE.get("running") and STATE.get("end_time") is not None:
        remaining = max(0.0, float(STATE["end_time"]) - now)
        STATE["remaining_seconds"] = remaining
        if remaining <= 0:
            STATE["running"] = False
            STATE["end_time"] = None
            save_state()
    return max(0.0, float(STATE.get("remaining_seconds", 0)))


def public_state():
    with LOCK:
        materialize_remaining()
        payload = dict(STATE)
        payload["server_time"] = time.time()
        return payload


def authorized():
    provided = request.headers.get("X-Admin-Key", "")
    return bool(ADMIN_KEY) and provided == ADMIN_KEY


def clamp(value, low, high):
    return max(low, min(high, value))


@app.after_request
def set_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/")
def home():
    return send_from_directory(ROOT, "control.html")


@app.get("/control.html")
def control():
    return send_from_directory(ROOT, "control.html")


@app.get("/overlay.html")
def overlay():
    return send_from_directory(ROOT, "overlay.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "server_time": time.time()})


@app.get("/api/state")
def get_state():
    return jsonify(public_state())


@app.post("/api/state")
def update_state():
    if not authorized():
        return jsonify({"error": "Invalid admin key"}), 401

    payload = request.get_json(silent=True) or {}

    with LOCK:
        now = time.time()
        materialize_remaining(now)
        action = payload.get("action", "update")

        try:
            if action == "start":
                if STATE["remaining_seconds"] <= 0:
                    STATE["remaining_seconds"] = STATE["duration_seconds"]
                if not STATE["running"]:
                    STATE["running"] = True
                    STATE["end_time"] = now + float(STATE["remaining_seconds"])

            elif action == "pause":
                materialize_remaining(now)
                STATE["running"] = False
                STATE["end_time"] = None

            elif action == "reset":
                STATE["running"] = False
                STATE["end_time"] = None
                STATE["remaining_seconds"] = float(STATE["duration_seconds"])

            elif action == "set_time":
                total = clamp(float(payload.get("seconds", 0)), 0, 999 * 3600)
                STATE["duration_seconds"] = total
                STATE["remaining_seconds"] = total
                STATE["running"] = False
                STATE["end_time"] = None

            elif action == "adjust":
                delta = clamp(float(payload.get("seconds", 0)), -999 * 3600, 999 * 3600)
                remaining = clamp(materialize_remaining(now) + delta, 0, 999 * 3600)
                STATE["remaining_seconds"] = remaining
                if STATE["running"]:
                    STATE["end_time"] = now + remaining

            elif action == "update":
                for key in ("title", "subtitle", "host_name"):
                    if key in payload:
                        STATE[key] = str(payload[key])[:80]

                for key in ("primary_color", "secondary_color", "text_color"):
                    value = str(payload.get(key, ""))
                    if HEX_COLOR.match(value):
                        STATE[key] = value

                if "portal_speed" in payload:
                    STATE["portal_speed"] = clamp(float(payload["portal_speed"]), 0.2, 3.0)
                if "glow_strength" in payload:
                    STATE["glow_strength"] = clamp(float(payload["glow_strength"]), 0.1, 2.5)
                if "show_milliseconds" in payload:
                    STATE["show_milliseconds"] = bool(payload["show_milliseconds"])
                if "timer_only" in payload:
                    STATE["timer_only"] = bool(payload["timer_only"])

            else:
                return jsonify({"error": "Unknown action"}), 400

        except (ValueError, TypeError):
            return jsonify({"error": "Invalid value"}), 400

        save_state()
        return jsonify(public_state())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    app.run(host="0.0.0.0", port=port, threaded=True)
