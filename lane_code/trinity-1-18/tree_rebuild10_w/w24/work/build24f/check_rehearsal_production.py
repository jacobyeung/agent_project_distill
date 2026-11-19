"""Compare authenticated production metadata using native meta-only builders."""
from pathlib import Path
from copy import deepcopy
import sys, json, os
L=Path(__file__).resolve().parents[2]; D=L/'work/build24f'; R=D/'rehearsal3'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
import torch
torch.set_num_threads(2); torch.set_num_interop_threads(1)
from student_pilot import r1_handover as H, r1_persisted as P, trained_groups as G
ext=L.parent/'ext/m400real'
e=J.load(ext/'e.json'); n=J.load(L/'out/kit_n_go/k/n.json')
assert J.sha(ext/'e.json')==n['r1_training']['handover_receipt']['sha256']
assert e['pins']['artifact']==n['init_artifact']['artifact']
aliases={x['sha256']:str(ext/'files'/x['path'].lstrip('/')) for x in J.load(ext/'MANIFEST.json')['files'] if x['path'].endswith('.json')}
aliases[J.sha(ext/'e.json')]=str(ext/'e.json')
base=Path('/scratch/jjyeung/devs1c_models/cp1/base/config.json')
aliases[J.sha(base)]=str(base)
def get(pin):
    from student_pilot.p3_provenance import load,pinned
    return load(pinned(pin))
with P.scope(aliases):
    source=get(e['pins']['config']); prep=get(e['pins']['preparation'])
    artifact=get(e['pins']['artifact']); weights=get(e['pins']['full_weights'])
    # N's topology uses the same authenticated base, camera and depth metadata;
    # its config controls the recipe, overrides, attachments and initialization.
    target=deepcopy(n); target['preparation']=source['preparation']
    pm=H.donor_meta_model(source); nm=H.donor_meta_model(target)
    pt=H.trainable_group_table(source,pm); nt=H.trainable_group_table(target,nm)
    names={k:sorted(v) for k,v in G.parameters(nm).items()}
    recorded={k:v['names'] for k,v in artifact['trained_groups']['groups'].items()}
    results=dict(source_target_equal=pt==nt, export_training_equal=weights['training']==nm.full_ft_report,
                 export_auxiliary_names_equal=names==recorded,
                 production_untied=nm.lm_head.weight is not nm.get_input_embeddings().weight)
    R.mkdir(exist_ok=True)
    J.write(R/'PRODUCTION_GROUPS.json',dict(status='PASS' if all(results.values()) else 'BLOCKER',
        checks=results,artifact=e['pins']['artifact'],receipt=n['r1_training']['handover_receipt'],
        source=pt,target=nt,recorded_training=weights['training'],constructed_training=nm.full_ft_report,
        recorded_auxiliary_names=recorded,constructed_auxiliary_names=names,
        target_preparation_basis='Pinned P camera/depth/base metadata with N config recipe/overrides/attachments; no weights read'))
    print(json.dumps(results),flush=True)
    assert all(results.values()), 'PRODUCTION LAUNCH BLOCKER: trainable topology differs'
