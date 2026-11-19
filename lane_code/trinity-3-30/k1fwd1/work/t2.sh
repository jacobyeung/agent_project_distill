K=/scratch/jjyeung/orch_n30/k1_ops3/work/partb
cd $K; ls -la build7 | head -40; for d in build7/*/; do echo "-- $d"; ls -la $d | head -20; done
head -c 1500 submit7.sh | cut -c1-300; echo; grep -n "sbatch\|scp\|ossh\|--time\|--gres\|-p \|partition" submit7.sh | cut -c1-300 | head -30
cat watch7.sh final7.sh canary7.sh own_pull_launch.py | cut -c1-300
cat /scratch/jjyeung/orch_n30/k1_ops3/STATUS_HEAD.md | head -60 | cut -c1-400
