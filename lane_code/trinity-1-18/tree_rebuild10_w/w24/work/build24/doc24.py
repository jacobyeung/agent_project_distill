from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24';sys.path.insert(0,str(D));import joblib as J
kits=J.load(D/'KIT.json');tree=J.load(L/'out/TREE_SEAL.json')['tree_sha256'];census=J.load(D/'CENSUS.json')
model=J.load(D/'proofs/resolver/real400.json')['model_files']
pins=dict(schema='build24-m600-pending-pins-v1',GO=False,template='work/build24/kits/n',step=600,
 plans={'A':{'directory':'/project/community/jjyeung/okh7/h_6ed2c7aa/m600','files':['h.json','RP.json','s.tar','DONE.json']},
        'B':{'directory':'/project/community/jjyeung/okh7/pb_a5416871','files':['h.json','RP.json','pb_report.json']}},
 required={
 'export_tar':{'from':'l.json export and ordered objects','fields':['names','bytes','sha256','each part pool_path/bytes/sha256']},
 'artifact':{'from':'h.json pins.artifact','fields':['exact resolved path','sha256']},
 'handover_receipt':{'from':'h.json itself and RP.json','fields':['path','sha256','bytes','schema p-handover-v1','step 600','job_id','trainer_commit']},
 'persisted_files':{'from':'every h.json pins entry','fields':['pin label','exact resolved path','sha256']},
 'checkpoint_000600':{'from':'RP.json checkpoint and complete.json files','fields':['complete.json','replicated.pt',*[f'rng{i:03d}.pt' for i in range(4)],*[f'shards/rank{i:03d}.pt' for i in range(4)]],
     'rule':'Use the exact published checkpoint_000600 or checkpoint_000600_UUID path; no symlink resolution aliases.'},
 'model_manifest':{'from':'preparation.model','fields':['path','sha256','root','files']},
 'model_manifest_files':{'from':'every entry in model manifest files','expected_names_from_P400':sorted(model),
     'rule':'Fill every name/hash from the step600 manifest. Supply exact metadata paths, bytes and hashes in l.json metadata; the full export supplies trained weights.'}},
 invariants=['All identity comparisons remain enforced','VQA bindings and removal order unchanged','routing_opener_init=keep','step544 lineage unchanged','routing_slices=deferred_first_boundary','all deferred cells zero','GO=false'],
 fill_script='out/fill_m600.py',outputs=['filled kit','<kit>_resolved.json','<kit>_fill.json','<kit>_uploads.json'])
J.write(L/'out/M600_PINS.json',pins)
J.write(L/'out/N_LAUNCH_CONFIG.json',J.load(D/'kits/n/k/n.json'))
text=f'''Vehicle N’s MINIMAL kit is unsubmitted. GO remains false.
Tree: `{tree}`.
Proof q (400): `{kits['q']['kit_seal']}`.
Launch n (600): `{kits['n']['kit_seal']}`; four ranks, advanced partition.
N’s checkpoint configuration uses `proof_mode: train`; the same allocation supplies the canary proof.
Declaration: `r1_training.routing_slices: "deferred_first_boundary"`.
The 600 template requires authenticated handover pins; `out/fill_m600.py` fills and reseals it.

N’s first 200 steps start from P’s step-600 weights and run through absolute step 800.
N uses the same routing rows as vehicle P, job 172660: P’s regenerated S1 base only.
The 400 proof base has 47,898 rows; receipt ca0616db, database 4e8e6c04.
The 600 fill binds the base from P’s authenticated runtime config.
Distance call rate, unit conversions and camera wording should stay where step 600 leaves them; this is an expectation, not a measured outcome.
Recovery, absolute_distance, units, coverage_distance, coverage_units and camera_wording contribute zero new rows.
Their gates count from the boundary at which those slices enter.

| VQA change | Count |
|---|---:|
| Named-route removal list, after all existing lists | 109 matches; 107 newly removed |
| Direction half-turn twins through path (b) | +7,971 |
| Eligible direction rows | 47,837 → 55,808 |
| Eligible route-planning rows | 8,669 → 8,562 |

Build 22’s held-out wording exclusions remain active: 8 coverage wordings and 24 camera wordings.
The two absent head slots retain NOT_PRESENT; seven other component slots remain DEFERRED.
The pose family record remains bound; its 23 excluded venue rows stay excluded.
P’s trained opener rows and the step-544 lineage remain unchanged.
Relative-count rows and answer-prior weights wait for the first boundary.
Step-time patches remain absent/OFF; the frame-host alias patch waits for the first boundary.
The advanced allocation runs its own mode-q canary proof; production admission and review gates remain enforced.
'''
assert len(text.splitlines())<40;(L/'out/N_CARD_KIT_ROWS.md').write_text(text)
(L/'out/M600_HANDOVER.md').write_text('''Run `out/fill_m600.py` from the extracted build24 package. The template remains unlaunchable until the handover is authenticated.

Plan A reads exact files under `okh7/h_6ed2c7aa/m600`: `h.json`, `RP.json`, `s.tar`, `DONE.json`.
Plan B reads exact files under `okh7/pb_a5416871`: `h.json`, `RP.json`, `pb_report.json`, then the receipt’s exact metadata paths.
Both branches require `p-handover-v1` at integer step 600 and checkpoint closure. Step 200 refuses as `E56:200`. Step 400 retains its export-only branch.

Create an opaque `l.json` with three fields:
- `objects`: ordered export-part records, each with `name`, exact `pool_path`, `bytes`, and `sha256`.
- `export`: the ordered `names`, combined `bytes`, and combined `sha256`. Export names contain `6ed2c7aa_m600.tar`.
- `metadata`: model metadata records with exact `path` or `pool_path`, `bytes`, and `sha256`.

`python3 out/fill_m600.py --plan A --handover-dir /project/community/jjyeung/okh7/h_6ed2c7aa/m600 --listing /project/community/jjyeung/okh7/l.json --output-kit /LOCAL/n600`

For plan B, change `--plan` and the handover directory. Use a fresh output directory. No source or training-input change is allowed during filling.
The script verifies P’s pinned source/runtime identities, checkpoint and export closure, export parts, model metadata and routing base; then it reseals the kit and emits the resolved config, filled-pin record and upload inventory.
`M600_PINS.json` names every pending pin. Recompute the upload diff for the filled kit’s changed capsules and seals before transfer.
The inherited identity checks and all production admission gates remain enforced. GO stays false. The n allocation requests four GPUs on advanced and runs its own canary proof; no submission is performed by this script.
''')
J.write(L/'out/N_LAUNCH.json',dict(GO=False,kit='work/build24/kits/n',step=600,partition='advanced',nodes=1,gpus=4,ranks=4,launcher_tasks=1,
 configuration='out/N_LAUNCH_CONFIG.json',proof_mode='train',
 canary='Submit the launch allocation as its own mode-q proof after filling and independent review.',
 first_window={'start':600,'end':800,'new_routing_slices':0},step_time_patches='absent/OFF',frame_host_alias_patch='deferred_first_boundary',
 submission='Not submitted; no scheduler or network used.'))
print('Card lines',len(text.splitlines()),'model filenames',len(model))
