#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time

STATE_FILE = os.path.expanduser("~/.local/state/monitorctl/state.json")

ARRANGEMENTS = ["Extend right", "Extend left", "Above", "Below", "Mirror", "Turn off"]


def niri_outputs():
    out = subprocess.run(
        ["niri", "msg", "outputs"], capture_output=True, text=True, timeout=5
    ).stdout
    outputs = []
    cur = None
    for line in out.splitlines():
        line = line.rstrip()
        m = re.match(r'^Output "(.*)" \((.*)\)]$'.replace("]", ""), line) if False else re.match(r'^Output "(.*)" \((.*)\)$', line)
        if m:
            if cur:
                outputs.append(cur)
            cur = {
                "connector": m.group(2),
                "name": m.group(1),
                "mode": None,
                "pos": None,
                "size": None,
                "scale": None,
                "modes": [],
                "preferred": None,
            }
        elif cur is not None:
            m2 = re.match(r"\s*Current mode: (\S+) @ ([\d.]+) Hz(?: \((preferred)\))?", line)
            if m2:
                cur["mode"] = f"{m2.group(1)}@{m2.group(2)}"
            m3 = re.match(r"\s*Logical position: (-?\d+), (-?\d+)", line)
            if m3:
                cur["pos"] = (int(m3.group(1)), int(m3.group(2)))
            m4 = re.match(r"\s*Logical size: (\d+)x(\d+)", line)
            if m4:
                cur["size"] = (int(m4.group(1)), int(m4.group(2)))
            m5 = re.match(r"\s*Scale: ([\d.]+)", line)
            if m5:
                cur["scale"] = float(m5.group(1))
            m6 = re.match(r"\s*(\d+)x(\d+)@([\d.]+)(?: \(current, preferred\)| \(preferred\)| \(current\))?$", line)
            if m6:
                mode = f"{m6.group(1)}x{m6.group(2)}@{m6.group(3)}"
                if mode not in cur["modes"]:
                    cur["modes"].append(mode)
                if "preferred" in line and cur["preferred"] is None:
                    cur["preferred"] = mode
    if cur:
        outputs.append(cur)
    return outputs


def by_connector(outputs):
    return {o["connector"]: o for o in outputs}


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def compute_position(target, outputs, arrangement):
    others = [o for o in outputs if o["connector"] != target["connector"]]
    if not others:
        return (0, 0)
    w, h = target["size"]
    if arrangement == "Extend right":
        ref = max(others, key=lambda o: o["pos"][0] + o["size"][0])
        mod = ref["pos"][1]
        return (ref["pos"][0] + ref["size"][0], mod)
    if arrangement == "Extend left":
        ref = min(others, key=lambda o: o["pos"][0])
        return (ref["pos"][0] - w, ref["pos"][1])
    if arrangement == "Above":
        ref = min(others, key=lambda o: o["pos"][1])
        return (ref["pos"][0], ref["pos"][1] - h)
    if arrangement == "Below":
        ref = max(others, key=lambda o: o["pos"][1] + o["size"][1])
        return (ref["pos"][0], ref["pos"][1] + ref["size"][1])
    return (0, 0)


def apply(target_connector, arrangement, mode=None, scale=None, dry=False):
    outputs = niri_outputs()
    target = by_connector(outputs).get(target_connector)
    if arrangement == "Turn off":
        cmd = ["niri", "msg", "output", target_connector, "off"]
        print("+ " + " ".join(cmd))
        if not dry:
            subprocess.run(cmd, capture_output=True, text=True)
        return
    if target is None:
        print(f"error: output {target_connector} not found")
        sys.exit(1)
    if arrangement == "Mirror":
        others = [o for o in outputs if o["connector"] != target_connector]
        ref = others[0] if others else None
        if mode or ref:
            mode0 = mode or ref["mode"] if ref else mode
            if mode0:
                cmd = ["niri", "msg", "output", target_connector, "mode", mode0]
                print("+ " + " ".join(cmd))
                if not dry:
                    subprocess.run(cmd, capture_output=True, text=True)
        if scale or ref:
            scale0 = scale or ref["scale"] if ref else scale
            if scale0:
                cmd = ["niri", "msg", "output", target_connector, "scale", str(scale0)]
                print("+ " + " ".join(cmd))
                if not dry:
                    subprocess.run(cmd, capture_output=True, text=True)
        cmd = ["niri", "msg", "output", target_connector, "position", "0", "0"]
        print("+ " + " ".join(cmd))
        if not dry:
            subprocess.run(cmd, capture_output=True, text=True)
        return
    if mode:
        cmd = ["niri", "msg", "output", target_connector, "mode", mode]
        print("+ " + " ".join(cmd))
        if not dry:
            subprocess.run(cmd, capture_output=True, text=True)
    if scale:
        cmd = ["niri", "msg", "output", target_connector, "scale", str(scale)]
        print("+ " + " ".join(cmd))
        if not dry:
            subprocess.run(cmd, capture_output=True, text=True)
    outputs = niri_outputs()
    target = by_connector(outputs).get(target_connector)
    if target["size"] is None:
        print("error: could not resolve output geometry")
        sys.exit(1)
    x, y = compute_position(target, outputs, arrangement)
    cmd = ["niri", "msg", "output", target_connector, "position", str(x), str(y)]
    print("+ " + " ".join(cmd))
    if not dry:
        subprocess.run(cmd, capture_output=True, text=True)


def prompt_for(connector, outputs, state):
    target = by_connector(outputs)[connector]
    saved = state.get(connector, {})
    modes = target["modes"] or [target["mode"]] if target["mode"] else []
    if target["preferred"] and target["preferred"] not in modes:
        modes.insert(0, target["preferred"])
    if not modes:
        modes = [target["mode"] or "keep"]
    modes_cb = "!".join(modes)
    try:
        default_arrange = ARRANGEMENTS.index(saved.get("arrange", "Extend right"))
    except ValueError:
        default_arrange = 0
    arrangement_items = "!".join(
        ("^" if i == default_arrange else "") + a for i, a in enumerate(ARRANGEMENTS)
    )
    scale = str(saved.get("scale", "1.0"))
    args = [
        "yad", "--form", "--center", "--title=New monitor connected",
        "--text=<b>%s</b> (%s) connected — how to display it?" % (connector, target["name"]),
        "--field=Arrange:CB", arrangement_items,
        "--field=Resolution:CB", modes_cb,
        "--field=Scale:NUM", "%s!0.5..3!0.05!" % scale,
        "--button=Apply:0", "--button=Cancel:1",
        "--button=Cancel only for now:9",
    ]
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=300).stdout
    except Exception:
        return
    if out is None:
        return
    parts = out.strip().split("|")
    if len(parts) < 3:
        return
    arrangement, mode, scale_value = parts[0], parts[1], parts[2]
    if arrangement == "Turn off":
        apply(connector, "Turn off")
    else:
        if not mode or mode == "keep":
            mode = None
        scale_parsed = None
        try:
            scale_parsed = float(scale_value)
        except ValueError:
            scale_parsed = saved.get("scale")
        apply(connector, arrangement, mode or None, scale_parsed or None)
    state[connector] = {"arrange": arrangement, "mode": mode, "scale": scale_parsed}
    save_state(state)


def cmd_watch():
    state = load_state()
    known = None
    while True:
        try:
            outputs = niri_outputs()
        except Exception:
            time.sleep(2)
            continue
        present = {o["connector"] for o in outputs}
        if known is None:
            known = present
        else:
            new = present - known
            for conn in sorted(new):
                prompt_for(conn, outputs, state)
                known.add(conn)
        known = known - (known - present)
        time.sleep(2)


def cmd_outputs():
    for o in niri_outputs():
        print(f"{o['connector']}  {o['name']}  {o['pos']}  {o['size']}  scale={o['scale']}  mode={o['mode']}")


def main():
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "outputs"
    if cmd == "watch":
        cmd_watch()
    elif cmd == "outputs":
        cmd_outputs()
    elif cmd == "apply":
        args = [a for a in argv[1:] if a != "--dry"]
        dry = "--dry" in argv[1:]
        if len(args) < 2:
            print("usage: monitorctl apply <output> <arrange> [mode] [scale] [--dry]")
            sys.exit(1)
        arrange = args[1]
        mode = args[2] if len(args) > 2 and args[2] != "keep" else None
        scale = None
        if len(args) > 3:
            try:
                scale = float(args[3])
            except ValueError:
                scale = None
        apply(args[0], arrange, mode, scale, dry=dry)
    elif cmd in ("help", "--help", "-h"):
        print("usage: monitorctl watch|outputs|apply <out> <arrange> [mode] [scale]")
    else:
        print("usage: monitorctl watch|outputs|apply <out> <arrange> [mode] [scale]")
        sys.exit(1)


if __name__ == "__main__":
    main()