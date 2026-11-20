C=/scratch/jjyeung/orch_n30/lever1_c; M=/scratch/jjyeung/n30_mirror/lever1; mkdir -p $C/arch
cat > $C/arch/arch_run.sh <<'RUN'
set -u
C=/scratch/jjyeung/orch_n30/lever1_c; M=/scratch/jjyeung/n30_mirror/lever1; A=$C/arch; cd $A
echo "START $(date -u +%FT%TZ)"
{ echo "# k1x_inputs archive manifest (lever1, $(date -u +%FT%TZ)); source trinity-1-18 /scratch/jjyeung, mirror trinity-2-28 $M"; cat $M/k1x_inputs.tar.sha256; sha256sum $M/k1x_inputs2.tar; echo "## k1x_inputs.tar"; tar tvf $M/k1x_inputs.tar; echo "## k1x_inputs2.tar"; tar tvf $M/k1x_inputs2.tar; } > $M/MANIFEST.txt
gzip -9 -c $M/MANIFEST.txt > $A/k1x_inputs_20261120.MANIFEST.txt.gz
nice -n 19 tar cf - -C $M k1x_inputs.tar k1x_inputs2.tar MANIFEST.txt | nice -n 19 zstd -T16 -9 -q -o $A/k1x_inputs_20261120.tar.zst
echo "ZSTD rc=$? $(date -u +%FT%TZ)"
sha256sum k1x_inputs_20261120.tar.zst > k1x_inputs_20261120.tar.zst.sha256; cat k1x_inputs_20261120.tar.zst.sha256; ls -l k1x_inputs_20261120.tar.zst k1x_inputs_20261120.MANIFEST.txt.gz
SZ=$(stat -c %s k1x_inputs_20261120.tar.zst); SHA=$(cut -d' ' -f1 k1x_inputs_20261120.tar.zst.sha256)
JOB=$(/usr/bin/python3 -c "import json,base64,sys;print(base64.b64encode(json.dumps(dict(id='lever1_k1x_archive',transport='archive',source=dict(host='trinity-2-28',archive='$A/k1x_inputs_20261120.tar.zst',sha256='$SHA'),destination=dict(host='trinity-2-28',path='/data3/jjyeung/distill_archives/lever1/k1x_inputs_20261120.tar.zst'),expected_bytes=$SZ,tier=3,priority=900)).encode()).decode())")
/usr/bin/python3 -s /scratch/jjyeung/io_governor/copy_archive.py --job "$JOB" --receipt $A/COPY_RECEIPT.json
echo "COPY_DONE rc=$? $(date -u +%FT%TZ)"
RUN
ls /scratch/jjyeung/io_governor/copy_archive.py && tmux has-session -t iogov_agent && echo agent_ok
tmux new-session -d -s l1_arch "setsid bash $C/arch/arch_run.sh > $C/arch/arch_run.log 2>&1 < /dev/null"
sleep 3; cat $C/arch/arch_run.log
ls -la $C/r3 $C/r4; ls -t /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs | head -4
for d in $(ls -td /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*lever1* | head -2); do echo "== $d"; ls $d; tail -c 600 $d/transcript.log 2>/dev/null; done
