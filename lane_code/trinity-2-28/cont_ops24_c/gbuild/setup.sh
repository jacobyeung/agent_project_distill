set -u
C=/scratch/jjyeung/orch_n30/cont_ops24_c
test -e $C/gbuild && { echo "gbuild exists; not overwriting"; exit 3; }
mv $C/in1 $C/gbuild
cd $C && sort -k2 gt_sha_228.txt | md5sum
ls /scratch/jjyeung/envs/ 2>/dev/null; for p in /scratch/jjyeung/envs/*/bin/python /usr/bin/python3; do echo "$p $($p -c 'import sys,numpy;print(sys.version.split()[0],numpy.__version__)' 2>&1 | tail -1)"; done
tmux ls 2>/dev/null; pgrep -fa codex | grep -v pgrep | wc -l
tmux new -d -s c24_gbuild "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $C/gbuild $C/gbuild/BRIEF_GBUILD.md --model gpt-6-astra --effort high --label c24_gbuild --skip-git-check > $C/gbuild_dispatch.log 2>&1"
sleep 8; tmux ls | grep c24; head -20 $C/gbuild_dispatch.log
