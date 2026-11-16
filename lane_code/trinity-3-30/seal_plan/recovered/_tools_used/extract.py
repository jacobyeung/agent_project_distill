#!/usr/bin/env python3
"""Single-pass transcript filter: stdin JSONL -> raw store of relevant tool_use/tool_result/text items."""
import sys, json, re
out_path = sys.argv[1]
LANES = r"(rs_tree|rs_rows|rs_contracts|rs_cover|dx_census|b11_native|b6_build|b6_design|k1_build|k1_ops|official544|evalx|leg_s1_review|next_queue|nq_review|trace_ruling|policy_audit|dense_plan|tree_review|o3_cache|scene_evidence)"
LANE_RE = re.compile(r"(?<![A-Za-z0-9])" + LANES)
def text_of(c):
    if isinstance(c, str): return c
    if isinstance(c, list):
        return "\n".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in c)
    return json.dumps(c) if c is not None else ""
kept_ids = set(); n = 0; k = 0; bad = 0
with open(out_path, "w") as out:
    for line in sys.stdin:
        n += 1
        try: d = json.loads(line)
        except Exception: bad += 1; continue
        msg = d.get("message") or {}
        role = msg.get("role") or d.get("type")
        ts = d.get("timestamp"); side = d.get("isSidechain")
        content = msg.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        if not isinstance(content, list): continue
        for c in content:
            if not isinstance(c, dict): continue
            t = c.get("type"); rec = None
            if t == "tool_use":
                s = json.dumps(c.get("input"), ensure_ascii=False)
                if "orch_cd" in s or LANE_RE.search(s):
                    kept_ids.add(c.get("id"))
                    rec = {"kind": "tool_use", "id": c.get("id"), "name": c.get("name"), "input": c.get("input")}
            elif t == "tool_result":
                s = text_of(c.get("content"))
                if c.get("tool_use_id") in kept_ids or LANE_RE.search(s):
                    rec = {"kind": "tool_result", "id": c.get("tool_use_id"), "paired": c.get("tool_use_id") in kept_ids, "text": s}
            elif t == "text":
                s = c.get("text", "")
                if LANE_RE.search(s) or "orch_cd" in s:
                    rec = {"kind": "text", "role": role, "text": s}
            if rec:
                rec.update({"line": n, "ts": ts, "sidechain": side}); k += 1
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"lines={n} kept={k} bad={bad}", file=sys.stderr)
