# TB_CONTRACT: the traceback file b/a.py writes (kit half), for jn7.sh and the publisher (2026-11-21)

Kit: n_go built in W/w28fix (the seal follows in the fix4 result). Kit 4e29bdfb and older never write this file.

## Path
- Inside the job's sandbox: `/tmp/q_22c714e1/tb.txt`. b/a.py computes it as `Path(sys.argv[2]).resolve().parent/'tb.txt'`;
  j.sh passes `$Q_NS/p` as argv[2], so the file is `$Q_NS/tb.txt`, beside `$Q_NS/r.json` and `$Q_NS/n.json`.
- On the node, outside the sandbox: `$Q_ROOT/tb.txt`. j.sh binds the node folder onto the sandbox name with
  `--bind "$Q_ROOT" "$Q_NS"` (and `--bind "$Q_ROOT" "$Q_ROOT"`), so it is the folder where j.sh itself writes
  `$Q_ROOT/q.log` and `$Q_ROOT/rooms.log`. A shell entered with `srun --overlap` reads it at `$Q_ROOT/tb.txt`.

## When it is written
- Modes q and r only. a.py appends one record at the moment an exception is caught, before the refusal is published:
  1. the exception that ends `production_proof._run` in a refusal (the one whose text becomes `refusal` in
     `p/q/RESULT.json` and q0.json), whichever step raised it;
  2. an exception leaving one of a.py's wrappers (`where=selection` for the host selection, `where=host` for the host
     frame, `where=admit` for admit);
  3. an uncaught exception of a.py itself (`where=uncaught`), recorded by its excepthook before r0.json is written.
  The forward runs in-process without a wrapper; rule 1 records its exception (`where=refusal`).
- One exception gives one record, however many wrappers it passes.
- The file is complete when the a.py process has exited, so before j.sh runs d.py and o.py. The publisher can copy it
  at the point where it copies q.log.
- No exception recorded means no file. A missing `tb.txt` is normal on a job that admits; on a refusal it means the
  refusal did not come from an exception (a status other than ADMIT returned without one).

## Content and bound
- UTF-8 text, opened in append mode, one `write` per record. A record starts with the line
  `=== <UTC time> pid=<pid> where=<wrapper> <ExceptionType>`, then the call stack above the wrapper, then the full
  traceback with chained causes, then one empty line.
- Unscreened: tree and library file paths, module names and the raw exception text appear as they are. j.sh screens
  q.log through b/l.py; a.py does not screen tb.txt. If the copy under X/o/<job>/ must obey the no-word rule, the
  publisher screens it (`python3 -B b/l.py <kit>` reads stdin and writes the screened text); the node-local file stays raw.
- Bound: a.py never lets the file grow past 204800 bytes (200 KB). A record longer than 65536 bytes keeps its first
  16384 and last 49152 bytes; a record that would cross the 200 KB bound is cut there, and later records are dropped.
  The publisher may copy the file whole.
- Mode 0600, owned by the job user. a.py creates it; nothing in the kit reads, rotates or removes it. A rerun into the
  same `$Q_ROOT` appends after the earlier records.

## What the publisher half owes
- If `$Q_ROOT/tb.txt` exists when the job publishes: copy it to `X/o/<job>/tb.txt` (at most 204800 bytes).
- HOLD.txt names `$Q_ROOT/tb.txt` among the node-local paths.
