cd /scratch/jjyeung/orch_n30/native_r2 || exit 1
du -sh work/p9 work/pyextra work/wheels work/np226 work/meta work/direct builds/01_c8/work/* 2>/dev/null | sort -h | tail -25
ls -la sub/b07a20b364 work/obj work/full_c8r
cat builds/02_c8r/work/op_run.sh
tar cf - sub builds/02_c8r work/full_c8r work/base work/tree work/code9 work/ORCHARD_LEDGER.jsonl work/streams work/run_full.sh | ssh -o ConnectTimeout=20 trinity-3-30.ib "cd /scratch/jjyeung/orch_n30/b01_d0guard/work/from113 && tar xf -"
echo TAR_RC=$?
