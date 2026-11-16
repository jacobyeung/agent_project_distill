# Reviewer refute tests (copy only): code tree, rows and 4.json binding.
import copy,hashlib,io,json,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];D=H.parent/'d0';sys.path.insert(0,str(H/'tools'))
import derive_kit_h1 as dk
out=H/'rv/out';out.mkdir(exist_ok=False)
base=json.loads((H/'build/over_fx.json').read_text())
res={}
def attempt(name,over):
    try: r=dk.derive(D/'kitfull',out/name,over); res[name]=dict(admitted=True,identity=r['config_identity']); return r
    except (ValueError,KeyError) as e: res[name]=dict(admitted=False,error=str(e)[:200])
# Baseline must still derive the reviewed identity.
attempt('baseline',copy.deepcopy(base))
# A: a different tree (one byte in the trainer) with a self-consistent pin.
src=Path(base['code_tree']['archive']['path']);pin=json.loads(Path(base['code_tree']['pin']['path']).read_text())
buf=io.BytesIO();files={}
with tarfile.open(src) as tf, tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as nt:
    for m in tf:
        data=tf.extractfile(m).read()
        if m.name=='student_pilot/carrier_c1_run.py': data+=b'\n# altered\n'
        info=copy.copy(m);info.size=len(data);nt.addfile(info,io.BytesIO(data));files[m.name]=hashlib.sha256(data).hexdigest()
arc=out/'alt.tar.tmp';arc.write_bytes(buf.getvalue())
tree=dk.digest(files);name='t_'+tree[:16]+'.tar';arc2=out/name;arc.rename(arc2)
np=dict(pin,files=files,tree_sha256=tree,commit='sha256:'+tree,archive=dict(path=dk.KIT_LOGICAL+name,sha256=dk.sha(arc2)))
np['sources']={k:files[k] for k in pin['sources']};np['operation_sources']={k:files[k] for k in pin['operation_sources']}
(out/'alt7.json').write_text(json.dumps(np))
alt=copy.deepcopy(base);alt['code_tree']=dict(archive=dict(path=str(arc2),sha256=dk.sha(arc2)),pin=dict(path=str(out/'alt7.json'),sha256=dk.sha(out/'alt7.json')))
attempt('A_alt_tree_with_reviewed_4json',alt)
alt2=copy.deepcopy(alt);del alt2['add_k']['4.json']
r=attempt('A2_alt_tree_without_4json',alt2)
if r:
    sys.path.insert(0,str(out/'A2_alt_tree_without_4json/b'))
    a=json.loads((out/'A2_alt_tree_without_4json/k/4.json').read_text());c=json.loads((out/'A2_alt_tree_without_4json/k/0.json').read_text())
    res['A2_alt_tree_without_4json']['inherited_4json_source_revision_matches_commit']=a.get('source_revision')==c['commit']
# B: different rows (routing stream pin changed) with the reviewed 4.json.
rows=copy.deepcopy(base);rows['config']['streams']['vqa']=dict(path=rows['config']['streams']['vqa']['path'].replace('receipt.json','receipt2.json'),sha256='0'*64)
attempt('B_changed_rows',rows)
# C: h1 tweaks refused.
for nm,sub in [('C_force0',dict(scheduled_sampling=dict(force_from_step=0,max_own_probability=0.5))),('C_noh1',None),('C_ms300',dict(milestones=[100,300]))]:
    v=copy.deepcopy(base)
    if sub is None: del v['config']['h1']
    else: v['config'].update(sub)
    attempt(nm,v)
dk.write(H/'rv/rv_mut.json',res);print(json.dumps(res,indent=1))
