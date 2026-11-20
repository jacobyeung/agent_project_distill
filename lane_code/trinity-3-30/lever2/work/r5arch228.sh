C=/scratch/jjyeung/orch_n30/lever1_c; A=$C/arch5; mkdir -p $A; cd $C/nogt/out
tar cf $A/nogt_gt15_20261120.tar gt SHA256SUMS NOGT_REPORT.md REPRO_TOLERANCE.md && sha256sum $A/nogt_gt15_20261120.tar > $A/nogt_gt15_20261120.tar.sha256; cat $A/nogt_gt15_20261120.tar.sha256; ls -l $A
H=$(cut -d' ' -f1 $A/nogt_gt15_20261120.tar.sha256)
timeout 300 bash -c "cat $A/nogt_gt15_20261120.tar | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib 'M=/scratch/jjyeung/n30_mirror/lever1; mkdir -p \$M && cat > \$M/nogt_gt15_20261120.tar && cd \$M && sha256sum nogt_gt15_20261120.tar && mkdir -p nogt_gt15 && tar xf nogt_gt15_20261120.tar -C nogt_gt15 && (cd nogt_gt15 && sha256sum -c --quiet SHA256SUMS 2>&1 | tail -3; echo SUMS_RC=\$?) ; df -h /scratch | tail -1'"
echo MIRROR_RC=$? want $H
cat > $A/arch_run.sh <<'RUN'
set -u
C=/scratch/jjyeung/orch_n30/lever1_c; A=$C/arch5; cd $A
echo "START $(date -u +%FT%TZ)"
nice -n 19 zstd -T8 -9 -q -f -o nogt_gt15_20261120.tar.zst nogt_gt15_20261120.tar; echo "ZSTD rc=$?"
sha256sum nogt_gt15_20261120.tar.zst > nogt_gt15_20261120.tar.zst.sha256; cat nogt_gt15_20261120.tar.zst.sha256
SZ=$(stat -c %s nogt_gt15_20261120.tar.zst); SHA=$(cut -d' ' -f1 nogt_gt15_20261120.tar.zst.sha256)
JOB=$(/usr/bin/python3 -c "import json,base64,sys;print(base64.b64encode(json.dumps(dict(id='lever2_nogt_archive',transport='archive',source=dict(host='trinity-2-28',archive='$A/nogt_gt15_20261120.tar.zst',sha256='$SHA'),destination=dict(host='trinity-2-28',path='/data3/jjyeung/distill_archives/lever1/nogt_gt15_20261120.tar.zst'),expected_bytes=$SZ,tier=3,priority=900)).encode()).decode())")
/usr/bin/python3 -s /scratch/jjyeung/io_governor/copy_archive.py --job "$JOB" --receipt $A/COPY_RECEIPT.json
echo "COPY_DONE rc=$? $(date -u +%FT%TZ)"
RUN
ls /scratch/jjyeung/io_governor/copy_archive.py && tmux has-session -t iogov_agent && echo agent_ok
tmux new-session -d -s l2_arch5 "setsid bash $A/arch_run.sh > $A/arch_run.log 2>&1 < /dev/null"
sleep 20; cat $A/arch_run.log
