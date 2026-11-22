export TZ=UTC; date -u +%TZ; cd ~/a15o/f23
sacct -j 174374,174375,174376 -X -n -P -o JobID,State,NodeList,Start,End
for n in 2 3 4; do echo "== p$n"; grep -v "error:" p$n.out 2>/dev/null; done
done=$(ls p?.out 2>/dev/null | wc -l)
if [[ $done == 5 ]] && ! squeue -h -j 174376 2>/dev/null | grep -q .; then
  models=$(grep -h 'model name' p?.out | sort -u | wc -l); sha=$(grep -h '^flags' p?.out | sort -u | wc -l)
  N=orchard-community-3
  if [[ $models != 1 || $sha != 1 ]]; then N=orchard-community-$(for n in 0 1 2 3 4; do echo "$(grep -oE '[0-9.]+ GB/s' p$n.out | cut -d' ' -f1) $n"; done | sort -n | head -1 | cut -d' ' -f2); fi
  echo "models $models flagsets $sha -> node $N"
  sbatch -p preempt -w $N -N1 -n1 -c 8 --mem=32G -t 01:10:00 --no-requeue --job-name a15_cot_apc6b14e700ea2 -o ~/a15o/f23/main_%j.out ~/a15o/f23/job.sh
  sleep 20; squeue -u jjyeung -h -o '%i|%j|%T|%N|%r|%M' | grep c6b14e
else echo "probes not finished; not submitted"; squeue -u jjyeung -h -o '%i|%j|%T|%N|%r' | grep c6b14e; fi
