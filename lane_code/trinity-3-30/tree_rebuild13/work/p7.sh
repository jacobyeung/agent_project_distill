W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr1; ls $W/w23/out | tr '\n' ' '; echo
head -c 2500 $W/w23/out/UPLOADS_NEW.json; echo; cat $W/w23/out/MINIMAL_MERGE_NOTES.md | head -40; wc -l $W/w23/out/MINIMAL_TREE.patch; grep "^+++" $W/w23/out/MINIMAL_TREE.patch
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild23 | head -1); tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4 | cut -c1-300
