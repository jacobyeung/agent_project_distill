# usage: sed "s/172456/<jobid>/" fetch_tpl.sh > fetch.sh; timeout 150 bash ossh.sh 'bash -s' < fetch.sh > read1_items.jsonl  (read 1 journal, small)
J=172456
timeout 90 srun --jobid=$J --overlap -n1 -c1 --mem=1G bash -c 'cat $(find /tmp/a'$J'* -path "*reads/0/metadata/journals/4/0/items.jsonl" 2>/dev/null | head -1)'
