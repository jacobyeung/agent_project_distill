#!/bin/bash
# add_read.sh SRC READ_ID SET VEHICLE JOB PURPOSE REPORTED_BY [extra ingest args...]   (see HOWTO.md)
set -u
[ $# -ge 7 ] || { echo "usage: add_read.sh SRC READ_ID SET VEHICLE JOB PURPOSE REPORTED_BY [--inputs DIR] [--official] [--archive-partial]"; exit 64; }
C=/scratch/jjyeung/orch_n30/corpus; cd $C || exit 1
SRC=$1 RID=$2 SET=$3 VEH=$4 JOB=$5 PURP=$6 REP=$7; shift 7
[ "$(hostname -s)" = trinity-3-30 ] || { echo "run on trinity-3-30"; exit 1; }
mkdir -p stage2/meta; M=stage2/meta/$RID.json
python3 -c 'import json,sys; a=sys.argv[1:]; json.dump(dict(read_id=a[0],set=a[1],vehicle=a[2],job_id=int(a[3]) if a[3].isdigit() else a[3],purpose=a[4],reported_by=a[5],official=False),open(a[6],"w"),indent=1)' "$RID" "$SET" "$VEH" "$JOB" "$PURP" "$REP" $M
python3 tool/ingest_read.py ingest --source "$SRC" --read-id "$RID" --meta $M --out stage2 "$@" | tee -a stage2/ADD_READ.log
rc=${PIPESTATUS[0]}; [ $rc -eq 0 ] || { echo "ingest rc=$rc: nothing published"; exit $rc; }
for f in stage2/index/$RID*.json; do
  id=$(basename $f .json); case $id in *.orphans) continue;; esac
  python3 tool/corpus_score.py stage2/reads/$id.jsonl.gz --by question_type | python3 -c "import json,sys; d=json.load(sys.stdin); [print(a, round(100*x['overall']['mean_score'],2), {k:round(100*v['mean_score'],2) for k,v in x['groups'].items()}) for a,x in d['arms'].items()]"
  (cd pub && /usr/bin/python3 -s ../tool/pub.py $C/stage2/reads/$id.jsonl.gz reads/$id.jsonl.gz corpus_r_${id//./_} && /usr/bin/python3 -s pub.py $C/$f index/$id.json corpus_i_${id//./_}) | tail -2
  [ -f stage2/index/$id.orphans.jsonl.gz ] && (cd pub && /usr/bin/python3 -s ../tool/pub.py $C/stage2/index/$id.orphans.jsonl.gz index/$id.orphans.jsonl.gz corpus_o_${id//./_}) | tail -1
done
python3 tool/ingest_read.py index --out stage2
