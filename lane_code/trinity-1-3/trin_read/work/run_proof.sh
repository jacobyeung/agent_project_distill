# usage: bash run_proof.sh GPU TOKEN   (on the host that owns the card; card line RESULT written first)
cd /scratch/jjyeung/orch_n30/trin_read/build || exit 1
tmux new-session -d -s trr_proof "/usr/bin/python3 -B trinity_read.py proof --root ../root --gpu $1 --token $2 --repeat 2 --yield-glob '/scratch/jjyeung/orch_n30/trin_read/root/yield/*' > ../work/proof_$2.log 2>&1; echo EXIT=\$? >> ../work/proof_$2.log"
sleep 5; tmux has-session -t trr_proof && echo proof_started; head -5 ../work/proof_$2.log
