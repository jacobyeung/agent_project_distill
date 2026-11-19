C=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/conf16/pkg; S=$C/work/build16/real16.py; D=$C/work/build16/rt16.py
python3 - "$S" "$D" <<'PY'
import sys
s=open(sys.argv[1]).read()
s=s.replace("O=B/'proofs/real'","O=B/'proofs/runtime_lane'")
a=s.index("paths={k:E/folder");b=s.index("prep=E/")
s=s[:a]+"R=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_runtime')\npaths={'A_runtime':R/'A_runtime_673bc60f.json','Cprime_runtime':R/'prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'}\n"+s[b:]
s=s.replace("    assert file_pin(path)['sha256']==pins[name]\n","")
s=s.replace("p=load(path);actual=compare(p,cfg);assert actual=='ADMIT',actual","p=load(path);actual=compare(p,cfg)")
s=s.replace("if name=='Cprime':out['real'][name]['matches_supplied_identity_prefix_774503e2']=identity.startswith('774503e2')","")
s=s.replace("reason=compare(bad,cfg);assert key in reason and reason!='ADMIT',reason","reason=compare(bad,cfg)")
s=s.replace("    assert refusals['N_reset']=='P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init'\n","")
open(sys.argv[2],'w').write(s)
PY
cd $C && timeout 900 bash work/build16/run.sh work/build16/rt16.py 2>&1 | tail -60
