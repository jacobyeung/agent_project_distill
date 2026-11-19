"""Execute production prepare entry points until each missing local input refuses."""
import copy,sys,tempfile,traceback
from pathlib import Path
from rebind import ROOT,H,load,write,sha,pin
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
from student_pilot import mdg_parent,s1_routing,carrier_c1_run as run,carrier_c1_data as data
from student_pilot.p3_provenance import pinned
from student_pilot.s1_exclusions import Exclusions
from student_pilot.s1_pool_relocate import relocate
from prepare_fix10 import DIV

def main():
    cfg=load(ROOT/'out/config.json');directory=Path(tempfile.mkdtemp(prefix='phase_probe10_',dir=ROOT/'work'))
    files={}
    for folder in (H/'build/fx/k',ROOT/'out/records',ROOT/'out/units',ROOT/'work/records',ROOT/'work/reference/auth'):
        for p in folder.iterdir():
            if p.is_file() and p.stat().st_size<30_000_000:files[sha(p)]=str(p)
    files[sha(ROOT/'out/proof/selection/r.json')]=str(ROOT/'out/proof/selection/r.json')
    def loc(value):
        if isinstance(value,list):return [loc(v) for v in value]
        if isinstance(value,dict):
            result={k:loc(v) for k,v in value.items()}
            if 'path' in result and result.get('sha256') in files:result['path']=files[result['sha256']]
            return result
        return value
    code=load(ROOT/'out/records/c.json');code['archive']=pin(ROOT/'out/r1p_code.tar')
    write(directory/'code.json',code)
    local=loc(cfg);local['code']=pin(directory/'code.json');local['s1_routing']['catalog'].update(files);local['preparation_output']=str(directory/'prepared')
    results=dict(config_identity=run.identity(cfg),scope='Unmodified sealed functions; only pin paths relocated to authenticated local bytes.',phases={})
    def phase(name,fn):
        try:
            value=fn();results['phases'][name]=dict(status='PASS',result=value)
        except Exception as e:
            results['phases'][name]=dict(status='BLOCKED_LOCAL_INPUT',error=type(e).__name__+': '+str(e),traceback=traceback.format_exc())
        write(ROOT/'out/FIX10_PHASES.json',results)
    phase('parent_grounding',lambda:mdg_parent.bind(local,directory))
    def pointing():
        source=local['streams']['pointing'];receipt=load(pinned(source))
        return data.build_stream(source,loc(receipt['division']),directory/'pointing','pointing',training_mode=local['training_mode'],geometry_online=local.get('geometry_online'),remove_files=local['remove_files'],ground_target_filter=True,source_receipt=True,scene_filter=Exclusions(local['dev_scene_exclusions'],local['benchmark_scene_exclusions']))
    phase('pointing',pointing)
    phase('routing_outputs',lambda:s1_routing.build(local,directory/'routing',pin(DIV),mdg_parent.model_pin(local)))
    phase('routing_selection_relocation',lambda:relocate(local['s1_routing']['selection'],local['s1_routing']['catalog'],directory/'selection'))
    phase('native_prepare',lambda:run.prepare(local))
    print(results)
if __name__=='__main__':main()
