# Owner handover

Only `land_kit.py` changes against the installed round-3 tools. `INSTALLED_CHANGES.json`
pins its installed preimage (`c7b80359…`) and delivered SHA256. `sync_health.py`
(`f4b0cc83…`), `dry_count.py` (`14fd0d44…`), wrappers, and the hourly script stay identical.
The health loop already runs with `LCS_REVIEW2_FIXES=1`; this update needs no loop restart.
All new production checks require that switch, whose default remains OFF.

The coordinator's `work/realgit4_by_swarm_opt/run_py36.txt` and `run_py312.txt` record
3 tests, 0 skips per interpreter with `LCS_REVIEW2_FIXES=1` and `rc=0`. They prove a
successful landing, hourly kit preservation, failed-commit staging cleanup without moving HEAD,
and an origin-rejection STOP before the home push or receipts. Those logs cover the installed
round-3 source. The new package needs its own real-Git rerun; this dispatch runs no Git.

Before installation, run `python3 -I -c 'import lzma'` on trinity-3-30 in the environment
used by `land_kit.sh`. If `LCS_PYTHON` overrides python3, check that interpreter as well.
The top-level `import lzma` remains unconditional: missing `_lzma` fails closed at startup,
including with the review switch off. Both test interpreters pass this import.

The authorized Git owner runs this exact command on trinity-1-18 against the frozen delivery
source, using new local throwaway repositories under `realgit5_by_swarm_opt`:

```bash
(
set -euo pipefail
L=/scratch/jjyeung/orch_n30/so_git
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
mkdir -p "$L/work/realgit5_by_swarm_opt/py36" "$L/work/realgit5_by_swarm_opt/py312"
for TAG in py36 py312; do
  case "$TAG" in
    py36) PY=/usr/bin/python3 ;;
    py312) PY=/scratch/jjyeung/envs/p1cpu/bin/python ;;
  esac
  date -u
  nice -n 10 "$PY" -I -s -B -c 'import lzma'
  LCS_RUN_REAL_GIT_TESTS=1 LCS_REVIEW2_FIXES=1 \
    LCS_REAL_GIT_WORK="$L/work/realgit5_by_swarm_opt/$TAG" LCS_PYTHON="$PY" \
    nice -n 10 bash "$L/work/review_round4_source/tests/run_real_git_owner.sh" \
    2>&1 | tee "$L/work/realgit5_by_swarm_opt/run_$TAG.txt"
done
)
```

Expect 3 tests, 0 skips, `LCS_REVIEW2_FIXES=1`, `FAILED_COMMIT …=true`, and
`ORIGIN_REJECTION …=true` in each log. `pipefail` preserves a failing runner status.
Stop on failure; do not rerun killed work without the user's answer.

Check the installed `land_kit.py` preimage hash. Stage its replacement as a temporary file
in the same installed directory, verify the delivered hash, then rename it atomically over
the target. Only the owner installs. Keep `LCS_ENABLE_KIT_LANDING=1` and
`LCS_REVIEW2_FIXES=1` for kit commands. Installed files and services were not changed here.

Patch 06 upgrades the installed round-3 source, tests, and docs. Patches 01–03 rebuild
from the supplied inputs; patches 04 and 05 provide alternative upgrades from their pinned
bases. Each owner route produces the same tools/tests/docs. Choose one route;
do not stack the alternative upgrades. `PATCH_BASES.json` pins each patch and preimage.

## Review round 4: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| 1 LOW | Refuse mixed-case negative Verdict/Status lines and leading No-Go, while keeping prose and cross-references accepted. | `ReviewTests.test_f1_*` |
| 2 LOW | Check every 64-hex token on archive SHA lines, sha256sum lines, and archive hash-table rows; owner binding cannot override a mismatch. | `ReviewTests.test_f2_*`, all seven listed formats plus additional hash/table cases |
| 3 LOW | Skip both nested dry-count tests outside the orchestration tree before any fixture writes. | `CoveragePortabilityTests.test_f3_*` plus the two normal integration cases |
| 4 INFO | Refuse leading `~` in every test-mode fetch/push URL; retain and preflight lzma. | `RemoteTests.test_f4_*`, `DocumentationTests.test_f4_*`, and both interpreter import checks |
| 5 INFO | State the passed realgit4 hook evidence, current installed base and health switch, and exact dry-count refusal condition. | `DocumentationTests.test_f5_*`; report/evidence consistency check |

On origin refusal, the local commit remains: contact the user before the hourly can push it.
On a handled add/commit failure, the tool clears only kit staging and checks the index.
Inspect HEAD before moving an untracked kit aside. A killed process or failed cleanup needs
the user before the hourly. The tool neither stops services nor rewrites history.

Python 3.6 subprocess timeouts may still wait on a surviving grandchild's pipes.
The health monitor cannot recognize an hourly BLOCKER consumed before its first observation.
Archive hash tables fail closed if any 64-hex value in the table differs, including an unrelated
source hash in another column. Use a separate non-table paragraph for unrelated hashes.
No framework behavior is used by these standard-library tools.
