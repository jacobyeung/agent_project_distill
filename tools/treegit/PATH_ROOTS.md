# Lane-path roots for the trainer tree

`trainer/` must reach its inputs (weights, membership files, kit inputs) through one resolved root, not through literal lane folders. At the C3 head, 88 `*.py` files hold 159 literals of `/scratch/jjyeung/orch_`, `/home/jjyeung/` or `/data2/jjyeung/`; most point at `/scratch/jjyeung/orch_cd/...` on the lost node (for example `student_pilot/mdg_eval.py` `EVAL`, `SAM`; `student_pilot/mask_grounding_head.py` `STEM_WEIGHTS`). `tools/treegit/LANE_PATH_BASELINE.json` holds the per-file counts and `tools/tests/test_no_lane_paths.py` fails when any file's count rises or a new file gains one.

## Resolver for the next epoch's tree

1. One root per run. A module resolves a lane path as `root / <relative path>`, where `root` comes from, in order:
   - the kit manifest's `lane_root` field, when the run starts from a kit (the kit is the single source of truth on the batch host);
   - the environment variable `DISTILL_LANE_ROOT`, for runs on Trinity;
   - otherwise the module raises with the relative path it needed. There is no silent fallback to a literal lane folder.
2. One helper. The tree owner adds `student_pilot/lane_root.py` with `lane_root()` and `lane_path(rel)`; every module imports it instead of building `Path('/scratch/...')` at import time. Resolve lazily, inside the function that reads the file, so importing a module never touches a path.
3. No `sys.path` edits across lanes. Code another lane wrote enters the tree as files under `trainer/` at a build, not through `sys.path.insert(0, '/scratch/jjyeung/orch_cd/...')` or `RK_MDG_ROOT`-style overrides (61 files insert into `sys.path` today).
4. Pinned inputs keep their sha256 next to the relative path (as `STEM_SHA256` does), so moving the root never changes what is read.
5. Paths on the batch host never name a lane, the project or a Trinity folder; the kit maps opaque relative names to files.

## Converting

The tree owner lane converts files at its next build; this branch changes no file under `trainer/`. After a build lowers counts, regenerate the baseline in the same commit as the tree:

    python3 -m tools.treegit.lane_paths --root trainer --write-baseline

`--check` prints each file that rose; plain invocation prints the current counts.
