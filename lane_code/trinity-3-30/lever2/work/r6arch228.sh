C=/scratch/jjyeung/orch_n30/lever1_c; A=$C/arch6; mkdir -p $A; cd $C/nogt/out
tar cf $A/nogt_arkit7_20261120.tar gt/arkit_gt SHA256SUMS NOGT_REPORT.md REPRO_TOLERANCE.md CAPTURE_CHECKS.json REPRODUCTION.json ARKIT_ORDER_CHECKS.json && sha256sum $A/nogt_arkit7_20261120.tar > $A/nogt_arkit7_20261120.tar.sha256; cat $A/nogt_arkit7_20261120.tar.sha256; ls -l $A
H=$(cut -d' ' -f1 $A/nogt_arkit7_20261120.tar.sha256)
timeout 300 bash -c "cat $A/nogt_arkit7_20261120.tar | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib 'M=/scratch/jjyeung/n30_mirror/lever1; mkdir -p \$M && cat > \$M/nogt_arkit7_20261120.tar && cd \$M && sha256sum nogt_arkit7_20261120.tar && mkdir -p nogt_ark7 && tar xf nogt_arkit7_20261120.tar -C nogt_ark7 && ls nogt_ark7/gt/arkit_gt/gt | wc -l; df -h /scratch | tail -1'"
echo MIRROR_RC=$? want $H
cat > $A/arch_run.sh <<'RUN'
set -u
C=/scratch/jjyeung/orch_n30/lever1_c; A=$C/arch6; cd $A
echo "START $(date -u +%FT%TZ)"
nice -n 19 zstd -T8 -9 -q -f -o nogt_arkit7_20261120.tar.zst nogt_arkit7_20261120.tar; echo "ZSTD rc=$?"
sha256sum nogt_arkit7_20261120.tar.zst > nogt_arkit7_20261120.tar.zst.sha256; cat nogt_arkit7_20261120.tar.zst.sha256
SZ=$(stat -c %s nogt_arkit7_20261120.tar.zst); SHA=$(cut -d' ' -f1 nogt_arkit7_20261120.tar.zst.sha256)
JOB=$(/usr/bin/python3 -c "import json,base64,sys;print(base64.b64encode(json.dumps(dict(id='lever2_nogt_ark_archive',transport='archive',source=dict(host='trinity-2-28',archive='$A/nogt_arkit7_20261120.tar.zst',sha256='$SHA'),destination=dict(host='trinity-2-28',path='/data3/jjyeung/distill_archives/lever1/nogt_arkit7_20261120.tar.zst'),expected_bytes=$SZ,tier=3,priority=900)).encode()).decode())")
/usr/bin/python3 -s /scratch/jjyeung/io_governor/copy_archive.py --job "$JOB" --receipt $A/COPY_RECEIPT.json
echo "COPY_DONE rc=$? $(date -u +%FT%TZ)"
RUN
ls /scratch/jjyeung/io_governor/copy_archive.py && tmux has-session -t iogov_agent && echo agent_ok
tmux new-session -d -s l2_arch6 "setsid bash $A/arch_run.sh > $A/arch_run.log 2>&1 < /dev/null"
sleep 20; cat $A/arch_run.log
