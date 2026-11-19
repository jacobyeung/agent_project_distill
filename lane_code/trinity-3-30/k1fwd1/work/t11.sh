K=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
python3 -c "
import json;d=json.load(open('$K/out/DEPENDENCIES.json'));print(len(d));[print(k,v[:12]) for k,v in d.items() if 'boundaries' in k or 'native_kit' in k or 'student_pilot' in k][:40]
import collections;print(collections.Counter(k.rsplit('/',2)[0][-60:] for k in d).most_common(12))"
cat /scratch/jjyeung/k1/run_tower_sam_2/BINDING.json | head -c 3600; echo
R=/scratch/jjyeung/k1/own_170235; d=$(ls $R/native/probe | head -1); python3 -c "import json;p=json.load(open('$R/native/probe/$d/PHASE_COMPLETE.json'));print({k:(v if k!='sources' else len(v)) for k,v in p.items()})"
