# usage: bash work/mirror_cmd.sh NODE   (run from the lane folder; one ssh through tssh.sh)
N=$1; cd /scratch/jjyeung/orch_n30/b10_reserve
cat archive/R0_RESERVE_20261116.tar | bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh $N.ib 'set -e; hostname -s; F=$(df --output=avail -B1G /scratch | tail -1 | tr -d " "); echo free_GB=$F; [ "$F" -gt 160 ] || { echo LOW_SPACE; exit 3; }; M=/scratch/jjyeung/n30_mirror/b10_reserve; mkdir -p $M; [ ! -e $M/R0_RESERVE_20261116.tar ] || { echo EXISTS; exit 4; }; cat > $M/R0_RESERVE_20261116.tar.part; mv $M/R0_RESERVE_20261116.tar.part $M/R0_RESERVE_20261116.tar; sha256sum $M/R0_RESERVE_20261116.tar; df -h /scratch | tail -1'
echo rc=$?
