set -u
C=/scratch/jjyeung/orch_n30/lever1_c; A=$C/arch6; cd $A
echo "START $(date -u +%FT%TZ)"
nice -n 19 zstd -T8 -9 -q -f -o nogt_arkit7_20261120.tar.zst nogt_arkit7_20261120.tar; echo "ZSTD rc=$?"
sha256sum nogt_arkit7_20261120.tar.zst > nogt_arkit7_20261120.tar.zst.sha256; cat nogt_arkit7_20261120.tar.zst.sha256
SZ=$(stat -c %s nogt_arkit7_20261120.tar.zst); SHA=$(cut -d' ' -f1 nogt_arkit7_20261120.tar.zst.sha256)
JOB=$(/usr/bin/python3 -c "import json,base64,sys;print(base64.b64encode(json.dumps(dict(id='lever2_nogt_ark_archive',transport='archive',source=dict(host='trinity-2-28',archive='$A/nogt_arkit7_20261120.tar.zst',sha256='$SHA'),destination=dict(host='trinity-2-28',path='/data3/jjyeung/distill_archives/lever1/nogt_arkit7_20261120.tar.zst'),expected_bytes=$SZ,tier=3,priority=900)).encode()).decode())")
/usr/bin/python3 -s /scratch/jjyeung/io_governor/copy_archive.py --job "$JOB" --receipt $A/COPY_RECEIPT.json
echo "COPY_DONE rc=$? $(date -u +%FT%TZ)"
