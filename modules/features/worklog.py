#!/usr/bin/env python3
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

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
    ("ytmdesktop", "Media/Music"),
    ("nautilus", "System"),
    ("gnome", "System"),
    ("niri", "System"),
    ("noctalia", "System"),
    ("alacritty", "Terminal"),
]

DEFAULTS = {
    "dir": os.path.expanduser("~/Documents/Worklogs"),
    "ai": True,
}


def default_dir():
    return DEFAULTS["dir"]


def interactive():
    return sys.stdin.isatty()


def prompt(label, default):
    if not interactive():
        return default
    try:
        raw = input(f"{label} [{default}]: ").strip()
    except EOFError:
        return default
    return raw if raw else default


def prompt_yes(label, default):
    if not interactive():
        return default
    suffix = "Y/n" if default else "y/N"
    try:
        raw = input(f"{label} [{suffix}]: ").strip().lower()
    except EOFError:
        return default
    if not raw:
        return default
    return raw in ("y", "yes")


def data_dir():
    return os.environ.get("WORKLOG_DIR", default_dir())


def active_path():
    return os.path.join(data_dir(), "active.json")


def fmt_dur(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def iso(ts):
    return datetime.fromtimestamp(ts).astimezone().isoformat()


def read_active():
    try:
        with open(active_path()) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_active(info):
    os.makedirs(data_dir(), exist_ok=True)
    with open(active_path(), "w") as f:
        json.dump(info, f)


def cmd_start(project, base_dir, ai_enabled):
    if read_active():
        return "A session is already active (worklog status)."
    if interactive() and not project:
        project = prompt("Project name", "")
    project = project.strip() or "default"
    if interactive():
        base_dir = prompt("Save directory", base_dir)
    base_dir = os.path.abspath(os.path.expanduser(base_dir or "~"))
    if interactive():
        ai_enabled = prompt_yes("Use AI summary", ai_enabled)
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", project).strip("-") or "default"
    name = time.strftime("%Y-%m-%d_%H%M%S") + "_" + slug
    session_dir = os.path.join(base_dir, "sessions", name)
    os.makedirs(session_dir, exist_ok=True)
    raw_path = os.path.join(session_dir, "raw.jsonl")
    log_path = os.path.join(session_dir, "poller.log")
    proc = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "__poll", raw_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=open(log_path, "a"),
        start_new_session=True,
    )
    write_active(
        {
            "project": project,
            "start": time.time(),
            "base_dir": base_dir,
            "session_dir": session_dir,
            "raw": raw_path,
            "pid": proc.pid,
            "ai": ai_enabled,
        }
    )
    return f"Recording started: {project}\nSave dir: {base_dir}\nAI: {'yes' if ai_enabled else 'no'}\nRaw log: {raw_path}"


def heuristic_category(app, title):
    text = " ".join(str(x or "") for x in (app, title)).lower()
    for key, cat in FALLBACK_MAP:
        if key in text:
            return cat
    return "Other"


def poll_loop(raw_path):
    def term(signum=None, frame=None):
        sys.exit(0)

    try:
        signal.signal(signal.SIGTERM, term)
        signal.signal(signal.SIGINT, term)
    except ImportError:
        pass

    last = None
    while True:
        try:
            out = subprocess.run(
                ["niri", "msg", "--json", "focused-window"],
                capture_output=True,
                text=True,
                timeout=3,
            ).stdout.strip()
            data = json.loads(out) if out and out != "null" else None
            if data is not None:
                key = (data.get("app_id"), data.get("title"), data.get("workspace_id"))
            else:
                key = None
        except Exception:
            key = None
        now = time.time()
        if key != last:
            entry = {
                "ts": now,
                "app": data.get("app_id") if data else None,
                "title": data.get("title") if data else None,
                "ws": data.get("workspace_id") if data else None,
            }
            with open(raw_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            last = key
        time.sleep(1.0)


def analyze(raw_path, project, start_ts, stop_ts, ai_enabled):
    intervals = []
    with open(raw_path) as f:
        entries = [json.loads(line) for line in f if line.strip()]
    for i, e in enumerate(entries):
        end = entries[i + 1]["ts"] if i + 1 < len(entries) else stop_ts
        intervals.append(
            {
                "start": e["ts"],
                "end": end,
                "seconds": max(0, end - e["ts"]),
                "app": e.get("app"),
                "title": e.get("title"),
            }
        )
    if not intervals:
        intervals.append(
            {
                "start": start_ts,
                "end": stop_ts,
                "seconds": max(0, stop_ts - start_ts),
                "app": None,
                "title": None,
            }
        )
    total = sum(i["seconds"] for i in intervals)

    categorized = None
    ai_note = ""
    if ai_enabled:
        categorized, ai_note = ai_categorize(intervals, total)
    if categorized is None:
        categorized = []
        for i in intervals:
            cat = heuristic_category(i["app"], i["title"])
            categorized.append(
                {
                    "start": iso(i["start"]),
                    "end": iso(i["end"]),
                    "seconds": round(i["seconds"], 1),
                    "app": i["app"],
                    "title": i["title"],
                    "description": (i["title"] or "").strip(),
                    "category": cat,
                    "tags": [],
                }
            )
        if not ai_enabled:
            ai_note = ""
        else:
            ai_note = ai_note or "AI categorizer unavailable; used local heuristics."
    return categorized, total, intervals, ai_note


def ai_categorize(intervals, total):
    exe = shutil.which("opencode")
    if not exe:
        return None, ""
    payload = [
        {
            "start": iso(i["start"]),
            "end": iso(i["end"]),
            "seconds": round(i["seconds"], 1),
            "app": i["app"],
            "title": i["title"],
        }
        for i in intervals
    ]
    prompt = (
        "You are a time-tracking assistant. I will provide computer activity logs. "
        "Your goal: assign a single category and tags to each activity interval, and clean up descriptions.\n\n"
        "RULES:\n"
        "1. Return ONLY a raw JSON array. No conversational text, no code fences.\n"
        "2. Each item uses EXACTLY this schema: "
        '{"start": "ISO", "end": "ISO", "seconds": <number>, "app": "...", '
        '"title": "...", "description": "...", "category": "...", "tags": ["..."]}.\n'
        '3. Pick category ONLY from: ' + ", ".join(repr(c) for c in CATEGORIES) + ".\n"
        "4. 'description' = a cleaned up, human-readable activity summary derived from the title.\n"
        "5. Keep 'start', 'end' and 'seconds' exactly as provided. Never alter durations.\n"
        "6. Merge consecutive intervals that share the same theme (e.g. several Firefox entries about the same topic) "
        "by keeping the start of the first and the end of the last, summing seconds.\n"
        "7. 'tags' may contain extra labels (e.g. 'research', 'psp'), usually 0-2 items.\n"
        "8. The sum of all 'seconds' must equal the total session duration.\n\n"
        "INPUT (JSON array):\n" + json.dumps(payload) + "\n\n"
        "OUTPUT (JSON array only):\n"
    )
    cmd = [exe, "run", prompt]
    if os.environ.get("WORKLOG_AI_CMD"):
        import shlex

        cmd = shlex.split(os.environ["WORKLOG_AI_CMD"]) + [prompt]
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180, env=os.environ.copy()
        )
        text = out.stdout if out.returncode == 0 else ""
    except Exception as exc:
        return None, f"AI failed: {exc}"
    ary = extract_json_array(text)
    if ary is None:
        return None, "AI returned no parseable JSON."
    if abs(sum(e.get("seconds", 0) for e in ary) - total) > max(total * 0.02, 2.0):
        return None, "AI output durations drift from measured total; discarded."
    return ary, ""


def extract_json_array(text):
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end < start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def build_report(project, start_ts, stop_ts, categorized, ai_note, ai_enabled, session_dir):
    total = stop_ts - start_ts
    lines = []
    lines.append(f"# Worklog: {project}")
    lines.append("")
    lines.append(f"- **Started:** {iso(start_ts)}")
    lines.append(f"- **Ended:** {iso(stop_ts)}")
    lines.append(f"- **Total:** {fmt_dur(total)}")
    lines.append(f"- **Raw log:** `{os.path.join(session_dir, 'raw.jsonl')}`")
    lines.append(f"- **Categorized:** `{os.path.join(session_dir, 'activity.json')}`")
    lines.append("")

    cat_totals = {}
    for e in categorized:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["seconds"]
    lines.append("## Time by category")
    lines.append("")
    lines.append("| Category | Time | Share | Intervals |")
    lines.append("| --- | --- | --- | ---: |")
    count = {}
    for e in categorized:
        count[e["category"]] = count.get(e["category"], 0) + 1
    for cat in sorted(cat_totals, key=lambda c: -cat_totals[c]):
        share = 100.0 * cat_totals[cat] / total if total else 0.0
        lines.append(
            f"| {cat} | {fmt_dur(cat_totals[cat])} | {share:.1f}% | {count[cat]} |"
        )
    lines.append("")

    app_totals = {}
    for e in categorized:
        app = e.get("app") or "unknown"
        app_totals[app] = app_totals.get(app, 0) + e["seconds"]
    lines.append("## Time by application")
    lines.append("")
    lines.append("| Application | Time | Share |")
    lines.append("| --- | --- | ---: |")
    for app in sorted(app_totals, key=lambda a: -app_totals[a]):
        share = 100.0 * app_totals[app] / total if total else 0.0
        lines.append(f"| {app} | {fmt_dur(app_totals[app])} | {share:.1f}% |")
    lines.append("")

    lines.append("## Timeline")
    lines.append("")
    lines.append("| Start | End | Duration | App | Title | Category |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for e in categorized:
        app = e.get("app") or "unknown"
        title = (e.get("description") or e.get("title") or "").replace("|", "/")
        lines.append(
            f"| {e['start'][11:19]} | {e['end'][11:19]} | {fmt_dur(e['seconds'])} "
            f"| {app} | {title} | {e['category']} |"
        )
    lines.append("")

    lines.append("## AI insights")
    lines.append("")
    if not ai_enabled:
        lines.append("_AI disabled for this session._")
    elif ai_note.startswith("AI failed") or ai_note == "AI categorizer unavailable; used local heuristics.":
        lines.append(f"_{ai_note}_")
    else:
        insights = ai_insights(project, total, categorized)
        lines.append(insights if insights else "_AI insights unavailable._")
    return "\n".join(lines) + "\n"


def ai_insights(project, total, categorized):
    exe = shutil.which("opencode")
    if not exe:
        return ""
    summary = [
        {
            "category": e["category"],
            "app": e.get("app"),
            "description": e.get("description"),
            "seconds": e["seconds"],
        }
        for e in categorized
    ]
    prompt = (
        f"You are a work-session reviewer. The user closed a work session on project '{project}' "
        f"that lasted {fmt_dur(total)}.\n\n"
        "Write a short structured report (markdown, a few bullet sections, no fluff): "
        "what the session was mostly about, how time distributed across categories, "
        "any patterns (tool switching, long blocks), and one practical suggestion.\n\n"
        "CATEGORIZED ACTIVITY:\n" + json.dumps(summary) + "\n"
    )
    try:
        out = subprocess.run(
            [exe, "run", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            env=os.environ.copy(),
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def cmd_stop(args):
    active = read_active()
    if not active:
        return "No active session."
    _, flag_base, flag_ai = parse_flags(args)
    if interactive() and flag_base is None:
        new_base = prompt("Save directory", active["base_dir"])
    else:
        new_base = flag_base or active["base_dir"]
    new_base = os.path.abspath(os.path.expanduser(new_base or "~"))
    if flag_ai is not None:
        ai_prompted = flag_ai
    elif interactive():
        ai_prompted = prompt_yes("Use AI summary", active["ai"])
    else:
        ai_prompted = active["ai"]

    if new_base != os.path.abspath(active["base_dir"]):
        old_dir = active["session_dir"]
        new_dir = os.path.join(new_base, "sessions", os.path.basename(old_dir))
        os.makedirs(new_dir, exist_ok=True)
        for entry in os.scandir(old_dir):
            shutil.move(entry.path, os.path.join(new_dir, entry.name))
        active["session_dir"] = new_dir
        active["raw"] = os.path.join(new_dir, "raw.jsonl")
        active["base_dir"] = new_base

    pid = active.get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    time.sleep(0.4)
    stop_ts = time.time()
    categorized, _, intervals, ai_note = analyze(
        active["raw"], active["project"], active["start"], stop_ts, ai_prompted
    )
    session_dir = active["session_dir"]
    total = stop_ts - active["start"]
    with open(os.path.join(session_dir, "activity.json"), "w") as f:
        json.dump(
            {
                "project": active["project"],
                "start": iso(active["start"]),
                "end": iso(stop_ts),
                "total_seconds": round(total, 1),
                "ai": ai_prompted,
                "activities": categorized,
            },
            f,
            indent=2,
        )
    report = build_report(
        active["project"],
        active["start"],
        stop_ts,
        categorized,
        ai_note,
        ai_prompted,
        session_dir,
    )
    report_path = os.path.join(session_dir, "report.md")
    with open(report_path, "w") as f:
        f.write(report)
    try:
        os.remove(active_path())
    except FileNotFoundError:
        pass
    return (
        f"Session saved.\nCategorized: {session_dir}/activity.json\nReport: {report_path}\n"
        + ("Note: " + ai_note + "\n" if ai_note else "")
    )


def cmd_status():
    active = read_active()
    if not active:
        return "Not recording."
    elapsed = time.time() - active["start"]
    return f"Recording: {active['project']} ({fmt_dur(elapsed)} elapsed, AI {'on' if active['ai'] else 'off'})"


def cmd_toggle(args):
    if read_active():
        return cmd_stop(args)
    return cmd_start(join_args(args), default_dir(), True)


def join_args(args):
    return " ".join(a for a in args if not a.startswith("--"))


def parse_flags(args):
    project_parts = []
    base = None
    ai = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--ai":
            ai = True
        elif a == "--no-ai":
            ai = False
        elif a == "--dir":
            i += 1
            if i < len(args):
                base = args[i]
        elif a.startswith("--dir="):
            base = a[len("--dir="):]
        else:
            project_parts.append(a)
        i += 1
    return " ".join(project_parts), base, ai


def cmd_start_from_args(args):
    project, base, ai = parse_flags(args)
    return cmd_start(project, base or default_dir(), ai if ai is not None else True)


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "__poll":
        poll_loop(argv[1])
        return
    cmd = argv[0] if argv else "status"
    args = argv[1:]
    if cmd == "start":
        print(cmd_start_from_args(args))
    elif cmd in ("stop", "end"):
        print(cmd_stop(args))
    elif cmd == "toggle":
        print(cmd_toggle(args))
    elif cmd == "status":
        print(cmd_status())
    elif cmd in ("help", "--help", "-h"):
        print("usage: worklog start|stop|toggle|status [--dir=PATH] [--ai|--no-ai]")
    else:
        print("usage: worklog start|stop|toggle|status [--dir=PATH] [--ai|--no-ai]")
        sys.exit(1)


if __name__ == "__main__":
    main()