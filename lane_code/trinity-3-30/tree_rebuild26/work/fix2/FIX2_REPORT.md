# FIX2: forward runs in a fresh interpreter (option a)
Chose (a). `_run` looks `forward` up as a module global at call time (dis: LOAD_GLOBAL forward), so a.py swaps `production_proof.forward` for a wrapper before importing `run`. The wrapper starts a new interpreter that inherits no CUDA/driver state. (b) cannot cover direct driver calls such as triton.
I used `subprocess` exec of `sys.executable` with the parent's interpreter flags, not `multiprocessing` spawn: spawn re-runs the parent's `__main__` (b/a.py has no main guard), so the child would re-run the launch. Both start the same kind of fresh process.
The child receives the parent's sys.path, env (CUDA_VISIBLE_DEVICES as restored, TMPDIR/caches), cwd, umask, tempfile.tempdir, torch thread count, both r1_persisted context vars (merged `_paths`, `_proof`) and the job's RLIMIT_AS soft value (captured in a.py before `run`). It calls the native `forward`, which writes root/'f.json', and returns its dict over a private pipe or re-raises its exception.
Kit W/w26fix2/n_go: new seal 06d9a1b50d48f602986c487214c1bc035047518b2fb8decfb833b903b326eece (was b44a4915).
Files: b/a.py 23398417b89fd9c26e4348d60cc4382677174bf1a7aa09b684aa032a0c899947; b/fw.py (new) ae4d7c158011467168126a231497bb0c7768c189a854a7b3b90730efc7fbe987; SHA256SUMS.txt 06d9a1b5...; BUILD.json 94104fc9f7961148eebf701043faab0e572c8d631f17010a87cf7be6856c4b97 (payload differs only in kit_sha256).
Tar W/w26fix2/s26fix2_n_go.tar sha256 1dc17d1c697acc4786634b3a6274e08867c157a33f7afbad9baa4e73c47debda (prefix n_go/).
| Test (CPU, p1cpu torch 2.11 cpu, CVD='') | Result |
|---|---|
| T1 before: old kit, forward runs in-process (child pid = parent pid 1555965) | as expected |
| T1 after: a.py's real block installed (is_wrapper true); call via module global ran in child pid 1556029, ppid = parent 1555980 | PASS |
| T2 poisoned parent (device_count/is_available under CVD='', torch marker, soft AS lowered to 64 GiB, threads 3): child has no marker, cuda.is_initialized False, AS restored to job [-1,-1], CVD '', threads 3, same cwd/TMPDIR/tempdir/umask/scopes/proof/sys.path | PASS |
| T3 ValueError, KeyError, FileNotFoundError(errno, path), RuntimeError('No CUDA GPUs are available'): same type and message as in-process | PASS (4/4) |
| T3 child hard exit (os._exit 7) -> RuntimeError('child process exited with status 7 and no result'), caught by _run | PASS |
| T3 exception whose constructor rejects its args -> RuntimeError('<module>.<name>: msg') | differs, see below |
| T4 return dict equal to in-process except peak_rss_bytes; f.json bytes equal; same keys | PASS |
| T5 z.seal(new kit) = 06d9a1b5; diff -rq shows only a.py, fw.py (new), SHA256SUMS.txt, BUILD.json; a.py/fw.py parse; fw.py mode 644 like z.py | PASS |
Not covered or changed:
- No real forward was run: the tree's carrier module does not import in p1cpu (missing `trace_format`), so every test used a harness-only stub module in a test copy of the tree; the kit holds no test hook.
- `peak_rss_bytes` now measures the child process only, which excludes the parent's admission peak.
- RNG state is not carried; the forward does not seed when it runs without a journal.
- Context vars other than r1_persisted's two are not carried. Python-level monkeypatches in the parent are not carried either; none touch the forward path.
- An exception class whose constructor cannot be rebuilt from its args comes back as RuntimeError, which _run catches. In-process, such an exception would have escaped _run.
- The parent now holds its memory while the child loads the model, so the two processes' memory adds up. A child killed by a signal becomes a RuntimeError refusal instead of killing the job.
- A child left behind when the parent dies is killed through PR_SET_PDEATHSIG.
