#!/usr/bin/env python3
import glob
import json
import os
import shlex
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = [
    "Coding",
    "Browsing",
    "Meetings",
    "Communication",
    "Social Media",
    "Media/Music",
    "System",
    "Other",
]

FALLBACK_MAP = [
    ("firefox", "Browsing"),
    ("chromium", "Browsing"),
    ("brave", "Browsing"),
    ("whatsapp", "Communication"),
    ("discord", "Communication"),
    ("telegram", "Communication"),
    ("meet", "Meetings"),
    ("zoom", "Meetings"),
    ("webex", "Meetings"),
    ("vscode", "Coding"),
    ("code", "Coding"),
    ("nvim", "Coding"),
    ("neovim", "Coding"),
    ("opencode", "Coding"),
    ("spotify", "Media/Music"),
    ("youtube", "Media/Music"),
    ("nautilus", "System"),
    ("gnome", "System"),
    ("niri", "System"),
    ("noctalia", "System"),
    ("alacritty", "Terminal"),
]

PSP_TAGS = [
    "Paskaita/pratybos",
    "Skaitymas",
    "Planavimas",
    "Projektavimas",
    "Programavimas (kodavimas)",
    "Peržiūra",
    "Kompiliavimas",
    "Testavimas",
    "Atsiskaitymas",
    "PSP veikla",
]

BASE_DIR = Path(os.environ.get("WORKLOG_DIR", os.path.expanduser("~/Documents/Worklogs")))
ENV_FILE = Path(os.environ.get("WORKLOG_ENV", os.path.expanduser("~/.config/worklog/env")))
ACTIVITY = BASE_DIR / "activity.jsonl"
STATE = BASE_DIR / "state.json"
CURSOR = BASE_DIR / "cursor.json"
HISTORY_DIR = BASE_DIR / "history"
CLOCKIFY_BASE = "https://api.clockify.me/api/v1"
CLOCKIFY_WORKSPACE = os.environ.get("CLOCKIFY_WORKSPACE_ID", "69245cb76e6c848d15de4bcb")

MIN_DURATION = int(os.environ.get("WORKLOG_MIN_DURATION", "60"))
POLL_INTERVAL = float(os.environ.get("WORKLOG_INTERVAL", "1"))


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


def iso_z(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_from_z(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp()


def find_niri_socket():
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    candidates = sorted(glob.glob(os.path.join(runtime, "niri*.sock")))
    return candidates[-1] if candidates else None


def current_focus():
    env = os.environ.copy()
    cmd = ["niri", "msg", "--json", "focused-window"]
    for attempt in range(2):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3, env=env
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip()[:200])
            out = result.stdout.strip()
            data = json.loads(out) if out and out != "null" else None
            if data is None:
                return None
            return {
                "app": data.get("app_id"),
                "title": data.get("title"),
                "ws": data.get("workspace_id"),
                "ts": time.time(),
            }
        except Exception:
            if attempt == 0:
                sock = find_niri_socket()
                if sock:
                    env["NIRI_SOCKET"] = sock
                    continue
            return None
    return None


def write_activity(block, end_ts):
    duration = end_ts - block["start"]
    if duration < MIN_DURATION:
        return
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACTIVITY, "a") as f:
        f.write(
            json.dumps(
                {
                    "start_time": iso_z(block["start"]),
                    "end_time": iso_z(end_ts),
                    "duration": round(duration, 1),
                    "app": block.get("app"),
                    "title": block.get("title"),
                    "workspace": block.get("ws"),
                }
            )
            + "\n"
        )


def load_state():
    try:
        return json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_state(block):
    if block is None:
        try:
            STATE.unlink()
        except FileNotFoundError:
            pass
        return
    STATE.write_text(json.dumps(block))


def cmd_track():
    def term(signum=None, frame=None):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, term)
    signal.signal(signal.SIGINT, term)

    block = load_state()
    try:
        while True:
            focus = current_focus()
            if block and (focus is None or focus["app"] != block.get("app") or focus["title"] != block.get("title")):
                write_activity(block, time.time())
                save_state(None)
                block = None
            if focus and block is None:
                block = {
                    "app": focus["app"],
                    "title": focus["title"],
                    "ws": focus["ws"],
                    "start": focus["ts"],
                }
                save_state(block)
            time.sleep(POLL_INTERVAL)
    except SystemExit:
        if block:
            write_activity(block, time.time())
            save_state(None)


def read_pending():
    if not ACTIVITY.exists() or os.stat(ACTIVITY).st_size == 0:
        return [], 0
    lines = ACTIVITY.read_text().splitlines()
    cursor = 0
    try:
        cursor = int(CURSOR.read_text().strip())
    except (FileNotFoundError, ValueError):
        cursor = 0
    cursor = min(cursor, len(lines))
    return lines[cursor:], cursor


def aggregate(blocks):
    result = {}
    for b in blocks:
        key = (b.get("app"), b.get("title"))
        if key not in result:
            result[key] = {
                "app": b.get("app"),
                "title": b.get("title"),
                "duration": 0.0,
                "start": b["start_time"],
                "end": b["end_time"],
            }
        r = result[key]
        r["duration"] += b["duration"]
        if b["start_time"] < r["start"]:
            r["start"] = b["start_time"]
        if b["end_time"] > r["end"]:
            r["end"] = b["end_time"]
    return sorted(result.values(), key=lambda x: x["start"])


def clockify_headers(env):
    return {
        "X-Api-Key": env["CLOCKIFY_API_KEY"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def clockify_get(env, path):
    req = urllib.request.Request(
        CLOCKIFY_BASE + path, headers=clockify_headers(env)
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "[]")


def clockify_post(env, path, body):
    req = urllib.request.Request(
        CLOCKIFY_BASE + path,
        data=json.dumps(body).encode(),
        headers=clockify_headers(env),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode() or "{}"
            return r.status, json.loads(data)
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode()}


def fetch_context(env):
    wid = CLOCKIFY_WORKSPACE
    projects = clockify_get(env, f"/workspaces/{wid}/projects")
    tags = clockify_get(env, f"/workspaces/{wid}/tags")
    active_projects = {
        p["name"]: p["id"] for p in projects if not p.get("archived")
    }
    tags_by_name = {t["name"]: t["id"] for t in tags}
    return wid, active_projects, tags_by_name


def ensure_project(env, wid, name, projects_by_name):
    if name in projects_by_name:
        return projects_by_name[name]
    status, data = clockify_post(env, f"/workspaces/{wid}/projects", {"name": name})
    if status in (200, 201) and data.get("id"):
        projects_by_name[name] = data["id"]
        return data["id"]
    return None


def ensure_tag(env, wid, name, tags_by_name):
    if name in tags_by_name:
        return tags_by_name[name]
    status, data = clockify_post(env, f"/workspaces/{wid}/tags", {"name": name, "archived": False})
    if status in (200, 201) and data.get("id"):
        tags_by_name[name] = data["id"]
        return data["id"]
    return None


def ai_categorize(activities, projects_by_name, tags_by_name):
    exe = os.environ.get("WORKLOG_AI_CMD")
    if not exe and shutil_which("opencode"):
        exe = "opencode"
    if not exe:
        return None, "opencode not found"
    prompt = (
        "You are a time-tracking assistant. I provide computer activity logs. "
        "Map each activity to a Clockify project name and tags.\n\n"
        "CLOCKIFY CONTEXT:\n"
        f"PROJECTS: {json.dumps(sorted(projects_by_name))}\n"
        f"TAGS: {json.dumps(sorted(tags_by_name))}\n\n"
        "RULES:\n"
        "1. Return ONLY a raw JSON array. No conversational text, no code fences.\n"
        "2. Each item uses EXACTLY this schema: "
        '{"project": "<project name>", "description": "<cleaned summary>", '
        '"start": "ISO", "end": "ISO", "tags": ["<tag name>", ...]}.\n'
        "3. Prefer existing non-archived projects and tags from the context above. "
        "You may output new project/tag names that do not exist yet; they will be created.\n"
        "4. Group narrow window titles into broad categories ('Coding', 'Browsing', "
        "'Meetings', 'Social Media', 'Communication', 'Media/Music', 'System' or an existing project). "
        "Avoid names too specific to a single window title.\n"
        "5. If you choose a project whose name contains '#psp', attach EXACTLY ONE tag chosen from: "
        + ", ".join(repr(t) for t in PSP_TAGS) + ".\n"
        "6. Otherwise there can be multiple tags.\n"
        "7. Merge consecutive entries sharing the same theme by taking the first start and the last end.\n"
        "8. Keep 'start' and 'end' in yyyy-MM-ddTHH:mm:ssZ format. Never invent timestamps outside the input range.\n"
        "9. The sum of all durations must equal the total measured time.\n\n"
        "ACTIVITY:\n" + json.dumps(activities) + "\n\n"
        "OUTPUT (JSON array only):\n"
    )
    if os.environ.get("WORKLOG_AI_CMD"):
        cmd = shlex.split(os.environ["WORKLOG_AI_CMD"]) + [prompt]
    else:
        cmd = [exe, "run", prompt]
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180, env=os.environ.copy()
        )
        text = out.stdout if out.returncode == 0 else out.stderr
    except Exception as exc:
        return None, f"AI failed: {exc}"
    if not text.strip():
        return None, "AI returned no output"
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(text[text.find("[") : text.rfind("]") + 1])
    except Exception:
        return None, "AI returned no parseable JSON"
    if not isinstance(parsed, list):
        return None, "AI returned non-array JSON"
    total_measured = sum(a["duration"] for a in activities)
    total_mapped = 0
    for e in parsed:
        try:
            total_mapped += iso_from_z(e["end"]) - iso_from_z(e["start"])
        except Exception:
            pass
    if total_mapped and abs(total_mapped - total_measured) > max(total_measured * 0.05, 60):
        print(f"warning: mapped {total_mapped:.0f}s vs measured {total_measured:.0f}s")
    return parsed, ""


def shutil_which(name):
    for path in os.environ.get("PATH", "").split(os.pathsep):
        if not path:
            continue
        candidate = os.path.join(path, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def heuristic_map(entry):
    text = " ".join(str(x or "") for x in (entry.get("app"), entry.get("title"))).lower()
    for key, cat in FALLBACK_MAP:
        if key in text:
            return cat
    return "Other"


def push_entries(env, wid, entries, projects_by_name, tags_by_name):
    ok_ids = []
    entries = sorted(entries, key=lambda e: e.get("start", ""))
    for e in entries:
        try:
            start = iso_from_z(e["start"])
            end = iso_from_z(e["end"])
        except (KeyError, ValueError):
            print(f"skip: bad timestamps {e!r}")
            continue
        duration = end - start
        if duration < MIN_DURATION:
            continue
        project = e.get("project") or "Other"
        pid = ensure_project(env, wid, project, projects_by_name)
        if not pid:
            print(f"skip: could not resolve project {project!r}")
            continue
        tids = []
        for t in e.get("tags", []) or []:
            tid = ensure_tag(env, wid, t, tags_by_name)
            if tid:
                tids.append(tid)
        if "#psp" in project and tids:
            tids = tids[:1]
        body = {
            "description": (e.get("description") or "")[:3000],
            "start": iso_z(start),
            "end": iso_z(end),
            "projectId": pid,
            "tagIds": tids,
            "billable": False,
        }
        status, data = clockify_post(env, f"/workspaces/{wid}/time-entries", body)
        if status == 201:
            ok_ids.append(data.get("id") or "")
            print(f"ok: {body.get('description')!r} ({fmt_dur(duration)})")
        else:
            print(f"fail: {body.get('description')!r} -> {status} {data}")
    return len(ok_ids)


def fmt_dur(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def cmd_sync():
    env = load_env()
    if not env.get("CLOCKIFY_API_KEY"):
        print("CLOCKIFY_API_KEY missing in " + str(ENV_FILE))
        return 2

    pending, cursor = read_pending()
    if not pending:
        print("Nothing to sync.")
        return 0

    blocks = [json.loads(line) for line in pending if line.strip()]
    activities = aggregate(blocks)

    try:
        wid, projects_by_name, tags_by_name = fetch_context(env)
    except Exception as exc:
        print(f"clockify context failed: {exc}")
        return 2

    mapped, note = ai_categorize(activities, projects_by_name, tags_by_name)
    if mapped is None:
        print(note or "AI unavailable, using local heuristics")
        mapped = []
        for a in activities:
            cat = heuristic_map(a)
            mapped.append(
                {
                    "project": cat,
                    "description": (a.get("title") or "").strip(),
                    "start": a["start"],
                    "end": a["end"],
                    "tags": [],
                }
            )

    total = len(mapped)
    created = push_entries(env, wid, mapped, projects_by_name, tags_by_name)
    if created == total and total > 0:
        CURSOR.write_text(str(cursor + len(pending)))
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m")
        with open(HISTORY_DIR / f"{stamp}.jsonl", "a") as f:
            for line in pending:
                f.write(line + "\n")
        print(f"Synced {created}/{total} entries. Cursor advanced.")
    else:
        print(f"Pushed {created}/{total}. Cursor NOT advanced (retry on next sync).")
    return 0


def cmd_status():
    state = load_state()
    pending, cursor = read_pending()
    lines = []
    if state:
        elapsed = time.time() - state.get("start", time.time())
        lines.append(f"Recording: {state.get('app')} ({fmt_dur(elapsed)} since {iso_z(state['start'])})")
    else:
        lines.append("Not recording (tracker idle).")
    lines.append(f"Pending events: {len(pending)}")
    lines.append(f"Cursor: {cursor}")
    print("\n".join(lines))


def main():
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "status"
    args = argv[1:]
    if cmd == "track":
        cmd_track()
    elif cmd == "sync":
        return cmd_sync()
    elif cmd == "status":
        cmd_status()
    elif cmd in ("help", "--help", "-h"):
        print("usage: worklog track|sync|status")
        return 0
    else:
        print("usage: worklog track|sync|status")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())