#!/bin/bash
# Orchard login node under setsid nohup: fetch the camera return of 170846 and score it (complete 3-type prefix)
P=/project/community/jjyeung/bf94a7976a7e9; L=$P/a/score.log; export TZ=UTC
JOB=$(<"$P/a/8.txt"); RETURN=bf94a7976a7e9$(printf '%08x' "$JOB"); echo "start $(date -u +%TZ) return $RETURN" >> $L
cd $P && /usr/bin/python3 -I -s -B 3.py fetch --return-token "$RETURN" --out "$P/a/f" >> $L 2>&1; echo "fetch rc=$? $(date -u +%TZ)" >> $L
/usr/bin/python3 -I -s -B - "$P/a/f/0.tgz" >> $L 2>&1 <<'PY'
import csv,io,json,sys,tarfile
with tarfile.open(sys.argv[1]) as t:
    summary=json.load(t.extractfile('SUMMARY.json'))
    cards=json.load(t.extractfile('metadata/CARDS.json'))
    print('SUMMARY',json.dumps(summary)[:600])
    rows=list(csv.reader(io.StringIO(cards['query'])))
    print('CARDS',len(cards['visible']),rows[1:])
    assert summary['complete'] is True and summary['completed']==summary['expected']==1050
    assert len(cards['visible'])==1 and rows[1:] and all('H100' in row[1] for row in rows[1:])
    print('RETURN_OK')
PY
echo "check rc=$? $(date -u +%TZ)" >> $L
