from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';A=L/'attic/build24b/out';A.mkdir(exist_ok=True)
sys.path.insert(0,str(B));import joblib as J
kits=J.load(D/'KIT.json');cpu=J.load(D/'CPU_SUMMARY.json');uploads=J.load(L/'out/UPLOADS_24B.json');tree=kits['n']['tree_seal']
for name in ('N_CARD_KIT_ROWS.md','N_LAUNCH.json','N_LAUNCH_CONFIG.json','M600_PINS.json','M600_HANDOVER.md'):
 p=L/'out'/name
 if p.exists() and not (A/name).exists():p.rename(A/name)
card=f'''Vehicle N uses MINIMAL. GO remains false; the kit awaits independent review.
Init = P’s step-400 export `5083243c` from run `6ed2c7aa`, via the export-only receipt `b467c32b`.
No checkpoint or state after P’s step 400 initializes N. No handover fill remains.
Tree: `{tree}`.
Kit n: `{kits['n']['kit_seal']}`.
Kit q: `{kits['q']['kit_seal']}`.
Seal and pin sources: `work/build24b/KIT.json`, `out/M400_PINS.json`.

N requests advanced, four GPUs/four ranks and one launcher; the allocation runs its own mode-q canary.
Declaration: `r1_training.routing_slices: "deferred_first_boundary"`.
Init policy: `r1_training.init_policy: "step400_export_weights_fresh_v1"`.
The export supplies weights only. N starts a fresh optimizer and a fresh step counter at zero.
N’s first 200 steps therefore use local steps 1–200, including a fresh schedule and sampler position.
They start from P’s step-400 weights; they do not resume P’s optimizer or advance P’s counter to 600.

N keeps P’s routing stream: the regenerated S1 base, with receipt `ca0616db` and database `4e8e6c04`.
Recovery, absolute_distance, units, coverage_distance, coverage_units and camera_wording hold zero new rows.
Distance calls, unit conversions and camera wording receive no targeted new routing examples in this window.
Their behavior can still change through training; improvement is not established by the CPU fixture.
Routing-slice gates start at the boundary where those slices enter.

| VQA change against P | Count |
|---|---:|
| Named-route removal list after the existing lists | 109 matches; 107 newly removed |
| Direction half-turn twins, path (b) | +7,971 |
| Eligible direction rows | 55,808 |
| Eligible route-planning rows | 8,562 |
Counts and unchanged exclusion pins: `work/build24/CENSUS.json`.

Held-out wording exclusions, K1 removals and room rules remain active.
P’s trained opener rows stay `routing_opener_init=keep`; the step-544 lineage remains pinned.
The two absent head slots retain NOT_PRESENT; seven other slots stay DEFERRED, blocking official reads.
The pose record stays bound. Relative-count rows, answer-prior weights and the frame-host alias wait for the first boundary.
Step-time patches remain absent/OFF.
N launches without a freeze of the tower scale in the point-depth head. H3 can fire again at N’s first look for the same cause.
CPU evidence: `work/build24b/CPU_SUMMARY.json`; both kits ADMIT at init 400 and every rank has finite full-forward loss.
'''
assert len(card.splitlines())<40;(L/'out/N_CARD_KIT_ROWS.md').write_text(card)
J.write(L/'out/N_LAUNCH_CONFIG.json',J.load(B/'kits/n/k/n.json'))
J.write(L/'out/N_LAUNCH.json',dict(GO=False,kit='work/build24/kits/n',init_milestone=400,init_artifact=J.load(L/'out/M400_PINS.json')['artifact'],receipt='p-export-only-v1',
 partition='advanced',nodes=1,gpus=4,ranks=4,launcher_tasks=1,proof_mode='train',init_policy='step400_export_weights_fresh_v1',
 training_start_step=0,optimizer='fresh',tower_scale_freeze=False,first_window=dict(start=1,end=200,new_routing_slice_rows=0),
 canary='The same allocation runs mode q before the gated training launcher.',
 training='b/t.py invokes one torch.distributed.run with four workers; b/u.py checks the canary, exact configuration identity, and native admission.',
 approval='GO=false. Existing native host/review/admission/allocation checks remain mandatory. v.json supplies the independently admitted prepared config; no init pin is filled there.',
 configuration='out/N_LAUNCH_CONFIG.json',pins='out/M400_PINS.json',submitted=False))
operator='''The n kit binds P’s real step-400 export and export-only receipt. It requires no handover fill or step-600 file.
The q kit proves the same export. The n allocation requests advanced, four GPUs, four ranks and one launcher.

Apply the build24 stream first, then the files in `UPLOADS_24B.list`. The delta replaces the opaque source-archive filename already present in each kit, so it introduces no obsolete kit member. `SHA256SUMS.txt` must match the entire final kit directory.
The delta’s stream root is `work/build24b/upload`. `UPLOADS_24B.json` contains only added or changed files against both kit sets in `UPLOADS_MINIMAL.json`.

Resolve n on its host with the existing resolver interface:

```bash
python3 -I -s -B /project/community/jjyeung/okh7/x_22c714e1/n/b/resolve.py --pool /project/community/jjyeung/okh7 --output /project/community/jjyeung/okh7/x_22c714e1/rn.json
```

The optional listing argument can still name the existing listing. Without it, the resolver uses the four exact `x_22c714e1/w/0..3` paths and the existing `x_22c714e1/l.json` metadata inventory; if that inventory is absent, it uses the established `okh7/m/<sha256>` metadata paths. Every file remains checked against P’s authenticated metadata. The combined export length and hash are pinned in the kit. No runtime discovery changes a configuration pin or seal.
The small archive must contain the exact pinned MANIFEST.json and all its checked members. The raw s.tar and full metadata bytes were unavailable locally; verification of those bytes runs on the host.
DONE/e/r/RP and the small-file manifest are pinned. Only e/r admit the init; the checkpoint pointer in RP is never selected or loaded.

Pass the resolved record to n/job.sh through the normal submission workflow. The allocation stages data, runs the guard, then its own mode-q canary and room audit. With GO=false it trains no step.
The existing production approval must supply `/tmp/q_22c714e1/v.json`, the admitted prepared configuration, when GO is granted. It must retain the canary’s exact config identity and four ranks, and bind the native host/review receipts. Its preparation receipt must include the same r1_training inputs. All native review, source, preparation and allocation checks still run.
After the canary passes, the kit starts one launcher with `--nnodes=1 --nproc_per_node=4`; it supplies no resume checkpoint. No source acceptance check or admission gate is bypassed.

The guard requires at least 75 GiB, emits one sanitized diagnostic and refuses read failures with E42. No tower-scale freeze is configured.
No upload, submission, GPU execution or production approval was performed by this build.
'''
(L/'out/OPERATOR_24B.md').write_text(operator)
print('Card lines:',len(card.splitlines()))
