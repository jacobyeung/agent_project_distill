W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; sed -n 30,75p $W/w24z8b/out/kit_qdp/b/px.py; cd $W/work/d173912/173912; python3 -c "
import json;s=open('k_dr_r.json').read();i=s.find('c09bb5ca');print(s[max(0,i-400):i+200])"
