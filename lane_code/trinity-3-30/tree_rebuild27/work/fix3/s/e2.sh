W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
T=$W/w26fix/tree
{
echo "--- w26fix"; ls -la $W/w26fix
echo "--- w26fix2/work"; ls -la $W/w26fix2/work
echo "--- tree top"; ls -la $T; du -sh $T 2>/dev/null
echo "--- launch_r1"; ls -la $T/launch_r1 | head -80
echo "--- student_pilot count"; ls $T/student_pilot | wc -l
echo "--- kit k"; ls -la $W/w26fix2/n_go/k | head -40
echo "--- envs"; ls /scratch/jjyeung/envs/
echo "--- grep AutoProcessor / from_pretrained in tree"; grep -rn --include=*.py -E "from_pretrained|AutoProcessor|AutoTokenizer|AutoConfig|AutoModel|snapshot_download|hf_hub_download" $T/launch_r1 $T/student_pilot 2>/dev/null | grep -v "/tests\?/" | cut -c1-260 | head -120
} >&2
cd $W
tar czf - w26fix2/n_go/b w26fix2/n_go/job.sh w26fix2/n_go/SHA256SUMS.txt w26fix2/n_go/BUILD.json w26fix/tree/launch_r1/*.py w26fix/tree/student_pilot/decoupled_v_run.py w26fix/tree/student_pilot/carrier_c1_run.py w26fix/tree/student_pilot/r1_persisted.py w26fix/tree/student_pilot/p3_provenance.py 2>/dev/null
