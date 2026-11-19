cd /lab_data/tarrlab/jacoby/agent_project/aws_evac || exit 1
P='97a6a3eb|f2ad01ad|8865619b|5e1d07a4|1742c666|f02f16ad'
echo "== host $(hostname)"
echo "== map/ok hits"; grep -l -E "$P" _direct/map/*.json _direct/ok/*.json 2>/dev/null | head -50
echo "== members.tsv hits"; for f in d/new/*.members.tsv d/records/*.members.tsv; do n=$(grep -c -E "step_400/heads.json|m200/artifact.json|receipt.json|rows.sqlite" $f); [ "$n" != 0 ] && echo "$f $n"; done
grep -E "b19c1200/train/step_400/heads.json|49becb79/m200/artifact.json" d/new/97a6a3eb.tar.members.tsv | head
echo "== specific path hits in map"; grep -h -o -E "(97a6a3eb/runs/b19c1200/train/step_400/heads.json|f2ad01ad/runs/49becb79/m200/artifact.json|8865619b/u/7c9f2d84/receipt.json|5e1d07a4/f/h/r16/[a-z_.]+|1742c666/s/q127808/vxm_m4/receipt.json|f02f16ad/s/a[23]v[23]/[a-z_.]+|8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/[a-z]+/rows.sqlite)" _direct/map/*.json _direct/ok/*.json d/*/*.members.tsv 2>/dev/null | sort | uniq -c
echo "== other indexes"; ls _gcs3 _ret_ctl _ret_ctl/* 2>/dev/null | head -30
grep -c -E "$P" _gcs3/queue.tsv 2>/dev/null
for t in t1 t2 t3 t4 t5 t6 t7 d/t2 d/t4 d/t5 d/t6 kept_small/t4; do echo "$t $(ls $t 2>/dev/null | wc -l) $(ls $t 2>/dev/null | grep -c -E "$P")"; done
