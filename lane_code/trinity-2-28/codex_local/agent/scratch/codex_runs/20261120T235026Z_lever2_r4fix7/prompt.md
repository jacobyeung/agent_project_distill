# Fix: rank 4 CPU preflight 173952 returned its cause: stdlib module 'keyword' missing in the job's Python

Continue in `/scratch/jjyeung/orch_n30/lever1_c/r4kit/` under BRIEF_R4KIT.md, BRIEF_R4FIX*.md (last BRIEF_R4FIX6.md, the memory-guard change, which must stay), BRIEF_R4DBG.md (rules hold; FROZEN.json unchanged; local /scratch reads approved, do not stop to ask; no ssh/git/network/GPU/kill/Slurm; no /home or /data*).
The rerun preflight 173952 (token e71c940a6b283) staged ~66 GB onto ext4 job_tmp, then the worker died at launch (returncode 1, no signal; last stage input_pins; cgroup memory.current 69.4 GB, memory.peak 69.4 GB, oom 0). Its authenticated return is at `r4kit/returned_fail2/ret_c.tgz` (a0-hex JSON; launcher stderr_tail_hex decodes to):
```
Traceback (most recent call last):
  File "/scratch/jjyeung/b01ec87a6f29b/d/v/boot.py", line 13, in <module>
    runpy.run_path(args[0], run_name='__main__')
  File "<frozen runpy>", line 280, in run_path
  File "/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/lib/python3.12/pkgutil.py", line 3, in <module>
    from collections import namedtuple
  File ".../lib/python3.12/collections/__init__.py", line 35, in <module>
    from keyword import iskeyword as _iskeyword
ModuleNotFoundError: No module named 'keyword'
```
The same death probably killed 173926 silently. Find with file:line why the interpreter inside the job namespace lacks stdlib `keyword` (and which other stdlib modules are missing): e.g. a static pruner or allowlist that limits which environment/stdlib files are staged or bind-mounted, a namespace that exposes only listed files, or a staged env archive subset; compare with the D400 package (in/D400) whose read ran these items (job 173241) and how it exposed the interpreter. Fix it so the full stdlib of the pinned interpreter (and every package the worker imports) is available inside the namespace, without new deny-listed names on Orchard. Add a CPU test that starts the worker's real boot path inside the same namespace construction (or its closest local equivalent) and imports the complete set of modules the worker imports, including stdlib modules imported lazily (run `python -X importtime` or an import audit of the worker entry against the staged tree), and fails on any missing module.
One new opaque token; PLACE.md/REPORT.md/BUILD.json/FORECAST.json agree; all tests re-run. Final message: cause with evidence, fix, tests, token, delivery sha256 and bytes. Be quick.
