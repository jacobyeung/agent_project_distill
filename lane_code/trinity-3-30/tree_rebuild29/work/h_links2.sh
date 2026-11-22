export TZ=UTC; date -u +%TZ
# H, second call: verify the targets through the sandbox root of the job's rv.py and write the note (links were made at 03:25:47Z)
X=/project/community/jjyeung/okh7/x_22c714e1
timeout 150 srun --overlap --jobid 174246 -N1 -n1 bash -c '
D=/tmp/q_22c714e1_174246/rp/6ed2c7aa/m400
echo "readlink full_weights: $(readlink "$D/full_weights")"
echo "readlink heads.pt: $(readlink "$D/heads.pt")"
for p in $(pgrep -f "[b]/rv.py"); do
  R=/proc/$p/root
  if [ -d $R/tmp/q_22c714e1/p/q/w ]; then
    echo "sandboxed pid $p: $(tr "\0" " " < /proc/$p/cmdline | cut -c1-120)"
    echo "via sandbox runs: $(ls -la $R'"$X"'/runs/6ed2c7aa/m400 2>&1 | tail -n +2 | tr "\n" ";")"
    echo "target full_weights.json sha256: $(nice -n 10 sha256sum $R/tmp/q_22c714e1/p/q/w/full_weights.json | cut -c1-64) (pin 1de983c9)"
    echo "target heads sha256: $(nice -n 10 sha256sum $R/tmp/q_22c714e1/p/q/u/e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7 | cut -c1-64) (pin e72208ac)"
    break
  fi
done' < /dev/null
cat > $X/o/174246/MANUAL_LINKS_NOTE.txt <<NOTE
MANUAL LINKS NOTE, job 174246 (option H, ORCH RULING 2026-11-22T02:48Z, ORCH ANSWER 03:26Z). Links made by lane tree_rebuild29 at 2026-11-22T03:25:47Z (one srun --overlap call); targets hashed and this note written at $(date -u +%FT%TZ) in a second call, because the first call's srun consumed the rest of its script.
Why: ranks 1-3 load the init with verify_assets off and read the init artifact's raw paths under X/runs/6ed2c7aa/m400, where j.sh binds the empty Q_ROOT/rp; rank 0 alone relocates by sha256 to the staged copies. Without these links training fails at load_model on ranks 1-3.
Commands (one srun --overlap --jobid 174246):
  D=/tmp/q_22c714e1_174246/rp/6ed2c7aa/m400; mkdir -p "\$D"
  ln -s /tmp/q_22c714e1/p/q/w "\$D/full_weights"
  ln -s /tmp/q_22c714e1/p/q/u/e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7 "\$D/heads.pt"
Targets and hashes: p/q/w holds full_weights.json sha256 1de983c9 (the artifact's full_weights pin), model.safetensors.index.json 0b9c2646 and 5 shards (18,819,721,016 B), each equal to its manifest (n_review1k); p/q/u/e72208ac... equals the artifact's heads pin e72208ac. Init artifact p/q/u/5083243c, carrier-c1-artifact-v1, step 400, milestone 6ed2c7aa m400, as v.json init_artifact pins. Lane check at note time: see the RESULT LINKS OK/FAILED of tree_rebuild29.
Checked: fix18 (tree_rebuild29 subagent) found the cause on the node; n_review1k (RESULT 2026-11-22T02:50Z) hashed the targets on the node and read every reader of X/runs and rp in kit and tree (none follows the links or counts their bytes); the rehearsal with the same links in scratch passed two steps on four ranks with finite losses (RESULT 03:19Z).
No byte of the init, rows or code changed. For the first boundary: fix T in the tree (relocation on the verify-off branch).
NOTE
echo "note: $(wc -c < $X/o/174246/MANUAL_LINKS_NOTE.txt) B"; date -u +%TZ
