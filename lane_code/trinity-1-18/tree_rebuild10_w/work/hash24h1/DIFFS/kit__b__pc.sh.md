# kit/b/pc.sh

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 1 launch lines removed; 0 rehearsal lines added. Functions: launch tk_live_finish; rehearsal tk_live_finish.

```diff

--- launch/kit/b/pc.sh
+++ run4/kit/b/pc.sh
@@ -27,7 +27,6 @@
 # Do not archive files while an unfinished trainer can still modify them.
         timeout --signal=TERM --kill-after=5 150 python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --small || true
     fi
-    python3 -B -I -s "$ROOT/b/ep.py" "$ROOT" "$N" "$SLURM_JOB_ID" "$status" || true
     exit "$status"
 }
 trap 'tk_live_finish $?' EXIT

```

run5: 1 launch lines removed; 0 rehearsal lines added. Functions: launch tk_live_finish; rehearsal tk_live_finish.

```diff

--- launch/kit/b/pc.sh
+++ run5/kit/b/pc.sh
@@ -27,7 +27,6 @@
 # Do not archive files while an unfinished trainer can still modify them.
         timeout --signal=TERM --kill-after=5 150 python3 -B -I -s "$ROOT/b/pc.py" "$ROOT" "$N" "$SLURM_JOB_ID" --small || true
     fi
-    python3 -B -I -s "$ROOT/b/ep.py" "$ROOT" "$N" "$SLURM_JOB_ID" "$status" || true
     exit "$status"
 }
 trap 'tk_live_finish $?' EXIT

```
