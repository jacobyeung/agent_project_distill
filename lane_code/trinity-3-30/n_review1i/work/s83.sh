W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
cd $K; grep -n "f1\.json\|'c%d\|c0\.json\|s2\.json\|population\.json\|reader_filters\|binding\.json\|indices\.json\|'f\.json'\|\"f\.json\"\|live/\|/live\|'live'\|\"live\"" b/*.py b/*.sh job.sh < /dev/null | cut -c1-240 | head -60
echo "== tree"; cd $T; grep -rn "f1\.json\|\"population\.json\"\|'population\.json'\|reader_filters\.json\|\"indices\.json\|'indices\.json\|binding\.json\|'f\.json'\|\"f\.json\"" --include=*.py launch_r1 student_pilot < /dev/null | cut -c1-240 | head -40
echo "== cs.py verify"; n=$(grep -n 'def verify' $K/b/cs.py < /dev/null | head -1 | cut -d: -f1); sed -n "${n},$((n+70))p" $K/b/cs.py < /dev/null | cut -c1-260
