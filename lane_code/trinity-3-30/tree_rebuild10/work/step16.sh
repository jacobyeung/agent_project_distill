W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf15; P="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 TMPDIR=$C/tmp
sed -i "s#DB='/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7#DB='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7#" $C/s/t4.py
(cd $C && ulimit -f 204800 && timeout 900 $P s/t4.py > t4.log 2>&1; echo "t4 rc=$?"; $P -c "import json;d=json.load(open('$C/N3_VARIANTS_C3.json'));print('variants',d['variants'],'refused',d['refused'],'leaks',len(d['leaks']),'extra_refused',sum(1 for v in d['extra'].values() if v['gate'] and v['reader']!='ADMIT'),'of',len(d['extra']))")
# build 16 workspace + dispatch
mkdir -p $W/w16 && cd $W/w16 && tar xf $W/w15/out/tree_rebuild_b15_67f8baf1.tar && sed -i "s#(PACKAGE_LINE)#(\`tree_rebuild_b15_67f8baf1.tar\`, sha256 5a133c2ec16b3b2afb0230fb62e7c11810eedea1a84791e05c1b722a20f15fa2, seal 67f8baf14b966a15b7d7a0efe64fc375632daee45d94f113f7b82f77d8a11480)#" $W/prompts/build16.md && grep -c PACKAGE_LINE $W/prompts/build16.md
free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
tmux has-session -t tr10_b16 2>/dev/null && echo EXISTS || tmux new -d -s tr10_b16 "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement $W/w16 $W/prompts/build16.md --model gpt-6-astra --effort high --label tree_rebuild16 --skip-git-check > $W/work/build16_dispatch.log 2>&1"
# mirror bundle: package + lane scripts (no outputs)
mkdir -p $W/mirror && cd $W && tar cf mirror/tr10_scripts_b15.tar --exclude='*/pkg' --exclude='*/tmp' --exclude='*.log' prompts work/conf15/cf15.sh work/conf15/s work/conf15/t11 work/loader_n work/cont_real work/stage51 work/conf13 inputs/p_configs inputs/records inputs/count ext/pk 2>/dev/null; ls -la mirror; sha256sum mirror/tr10_scripts_b15.tar
sleep 15; tmux ls | grep tr10
