cd /scratch/jjyeung/orch_n30/reader_r1/work/b1g
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
for t in out/tests/test_package.py out/tests/test_constraints.py work/test_b1.py work/test_select_stubs.py work/test_tower.py work/test_sequence.py out/test_tower_pair.py out/test_b1_report.py work/test_memo_binding.py work/test_module_selection.py work/test_operator_memory.py work/test_fixes.py work/test_return_cli.py work/reviewer_checks.py work/scan_delta.py work/audit_payload.py work/test_multitype_ab.py work/verify_delivery.py; do
  echo "=== $t"; $PY -B $t > /tmp/rr1_t.log 2>&1; rc=$?; tail -4 /tmp/rr1_t.log; echo "EXIT $rc $t"
done
echo "=== replay"; (cd /scratch/jjyeung/orch_n30/reader_r1/work/b1/in/replay && NP=8 OUT=/scratch/jjyeung/orch_n30/reader_r1/work/b1g/out/replay_lane.jsonl $PY -B /scratch/jjyeung/orch_n30/reader_r1/work/b1g/work/replay_patched.py > /tmp/rr1_rp.log 2>&1); echo "EXIT $? replay"
sed "s|out/replay_patched.jsonl|out/replay_lane.jsonl|" work/check_replay.py > work/check_replay_lane.py; $PY -B work/check_replay_lane.py > out/REPLAY_CHECK_lane.txt 2>&1; echo "EXIT $? check_replay_lane"; grep -E "mismatches|not_seen_pairs" out/REPLAY_CHECK_lane.txt | head -12
echo DONE
