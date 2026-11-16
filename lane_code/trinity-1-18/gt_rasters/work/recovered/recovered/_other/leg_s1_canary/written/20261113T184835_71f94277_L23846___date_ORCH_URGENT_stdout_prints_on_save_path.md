<!-- recovered by seal_plan: transcript=71f94277 line=23846 utc=2026-11-13T18:48:35.781Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_URGENT_stdout_prints_on_save_path.md heredoc_quoted -->
# ORCH, urgent: can a full project filesystem crash the trainer at its next save? Answer within 10 minutes, before anything else

Your analysis says the launcher inherits stdout and that save and export disk guards print. I checked the job's output file: at the step-1 save and export the trainer wrote two JSON lines to it, `{"event": "checkpoint_disk_guard", ...}` and `{"event": "export_disk_guard", ...}`. That file is on the project filesystem, which had 351 GB free at 18:46Z and is losing 100 to 240 GB per hour. Periodic saves come about every two hours (the next near 19:40Z, then 21:40Z); the step-50 export near 21:40Z; step 100 near 01:40Z.

On Linux NFS, the first write after the server runs out of space succeeds into the page cache, the asynchronous flush fails, and the next write on the same open file returns "no space left on device". So the second print after the filesystem fills can raise in Python.

From the sealed trainer source (`checkpoint_space.py`, `carrier_c1_run.py`, the launcher `b/i.py`, the supervisor `b/sg.py`), with file and line:

1. Every statement that writes to stdout or stderr on the normal path of a periodic save, an export, a milestone, and an ordinary step: is it `print` (with or without `flush=True`), `sys.stdout.write`, `logging`, `warnings`, or a C library message? Which process writes it (rank 0 only, every rank, the supervisor)?
2. Is stdout line-buffered, unbuffered or block-buffered in those processes (interpreter flags, `PYTHONUNBUFFERED`, explicit reconfigure)? With block buffering, when does the buffer actually reach the file?
3. For each such write: if it raises `OSError`, is it caught? If not, what dies (the rank, the whole launch through the supervisor) and is a checkpoint left complete or half written at that moment (is the guard's print before or after the state is written)?
4. Your conclusion in one line: after the filesystem fills, at which event would the trainer most likely fail, and is there any state that would survive on the node until the job ends.

One RESULT, at most 25 lines. Then go straight to the state-copy design (my 1836Z order): if the answer to 4 is "it can fail at a save", I will want that copy to run early, after the next save, not late.