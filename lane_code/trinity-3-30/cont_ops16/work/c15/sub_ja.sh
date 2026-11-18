set -uo pipefail
O=/project/community/jjyeung/okh7; IN=$O/i_bb09a77d; KH=$O/x_3b862883
date -u
TZ=UTC sacct -j 170035,170037 -X -n -o JobID,JobName%24,State,Start,End 2>&1 | head
Q=$(TZ=UTC squeue -u jjyeung -p general -h -o '%i %j %T' 2>&1)
echo "queued before ours: $Q"; echo "$Q" | grep -q a15_cot_ap543f18fd && { echo "job A already queued; NOT submitting"; exit 4; }
[ ! -e $O/r/1b235d89 ] && [ ! -e $IN/m.tar ] && [ "$(sha256sum < $KH/ANON_OK.json | cut -c1-16)" = 110ed5105720a836 ] && [ "$(sha256sum < $IN/r8/ja.sh | cut -c1-16)" = 61dacd80eb8699e8 ] || { echo "precondition failed; NOT submitting"; exit 4; }
cd $IN && TZ=UTC sbatch -J a15_cot_ap543f18fd -o /dev/null -e $KH/o/%j.err < r8/ja.sh 2>&1
sleep 5; TZ=UTC squeue -u jjyeung -p general -o '%.10i %.20j %.8T %.20S %R' 2>&1
