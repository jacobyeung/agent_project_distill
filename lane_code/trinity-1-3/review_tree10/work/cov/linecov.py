"""Run unittest modules from TREE and report whether target lines executed (sys.monitoring)."""
import sys, json, unittest, os
tree, out, targets, mods = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), sys.argv[4:]
sys.path.insert(0, tree); os.chdir(tree)
want = {os.path.join(tree, f): set(v) for f, v in targets.items()}
hit = {f: set() for f in want}
M = sys.monitoring; TOOL = 3
M.use_tool_id(TOOL, 'rev')
def line(code, ln):
    f = code.co_filename
    if f in want:
        if ln in want[f]: hit[f].add(ln)
        return None
    return M.DISABLE
M.register_callback(TOOL, M.events.LINE, line)
M.set_events(TOOL, M.events.LINE)
suite = unittest.defaultTestLoader.loadTestsFromNames(mods)
res = unittest.TextTestRunner(verbosity=0).run(suite)
M.set_events(TOOL, 0)
r = dict(tests=res.testsRun, failures=len(res.failures), errors=len(res.errors),
         hit={os.path.relpath(f, tree): sorted(v) for f, v in hit.items()},
         missed={os.path.relpath(f, tree): sorted(want[f] - hit[f]) for f in want},
         failed=[str(t) for t, _ in res.failures + res.errors][:20])
json.dump(r, open(out, 'w'), indent=1); print(json.dumps(r))
