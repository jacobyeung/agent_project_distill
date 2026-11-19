from pathlib import Path
import hashlib,ast,json
W=Path(__file__).resolve().parents[1];O=W/'out';T=W/'work/new'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=W.parent/'donor/out/READER_REQUEST.md';s=p.read_text()
s=s.replace("The trainer's `load_model` already attaches the donor from its prepared receipt. Readers that construct `CarrierC1` directly, including the separate runtime loader, must add the attach call themselves.","The trainer's `load_model` attaches the donor from its prepared receipt. Readers that construct `CarrierC1` directly must warm-start its private visual and attach the pinned donor before loading the export. The separate runtime loader needs the metadata steps below before its strict head load.")
s=s.replace('Run `bash out/REAL_WEIGHT_COMMAND.sh`', 'Run `PYTHON=/path/to/python bash out/REAL_WEIGHT_COMMAND.sh`')
s+='''
## Byte-identical reader sources (M2)

`feature_contract` hashes all bytes of the nine files below, including comments. The training tree and reader tree must use byte-identical versions of these files. Any later edit locks N's exports out unless the reader repins through a matching, reviewed binding migration. A reader that merely recalculates `feature_contract_sha256` still fails `verify_export`, because its settings no longer equal the artifact's settings. Retain the original pinned reader tree to read existing exports; a migration must consistently rebind the trusted source and exported metadata. Fail-closed enforcement remains enabled.

All paths below are relative to `student_pilot/`. `scale_donor.py` is added by this overlay and is absent from base seal 57a1f14d; no base hash exists for it.

| File | SHA256 at base seal 57a1f14d | SHA256 in PATCH_DONOR2 |
|---|---|---|
'''
module=ast.parse((T/'student_pilot/scale_donor.py').read_text());names=next(ast.literal_eval(x.value) for x in module.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FEATURE_FILES' for t in x.targets))
for name in names:
 b=W/'work/base/student_pilot'/name;n=T/'student_pilot'/name
 s+=f'| `{name}` | `{sha(b) if b.exists() else "MISSING (absent at base seal)"}` | `{sha(n)}` |\n'
s+='''
## Separate runtime strict-load sequence (M3)

After constructing and warm-starting the native model and calling `scale_donor.attach(model, binding)`, the runtime loader must execute this sequence, matching `carrier_c1_run.load_artifact`:

```python
heads = torch.load(heads_path, map_location="cpu", weights_only=True)
metadata = heads.pop("_scale_donor", None)
if metadata != artifact.get("scale_donor"):
    raise ValueError("Scale donor artifact/head metadata differs")
scale_donor.verify_export(model, heads, metadata)
model.auxiliary_heads.load_state_dict(heads, strict=True)
```

Attach alone fails: `_scale_donor` is metadata and cannot enter the strict state dictionary. The fixture runs the actual `mdg_runtime.load_runtime` strict-load call with this preprocessing, tests its failure without preprocessing, and rejects metadata/tensor corruption. The test substitutes bundle/model-loading boundaries and isolates `r2_policy.unsupported_entry`; production still requires an authenticated R2 reader adapter. This patch does not remove that legacy-reader guard or install that adapter.

## Preparation and checkpoint boundary (S1)

S1 remains documented, not implemented. Bind the donor before producing N's preparation. `prepare` includes it in the receipt and `prepared` rejects an existing receipt that omits it with `C1 preparation frame layout/LM lever differs`. A fresh receipt is required under this patch.

Treating the donor only as a preparation-free lever would not satisfy the requested native checkpoint-resume proof. `identity(cfg)` includes `scale_donor`; `train` binds that identity into the resume binding, and `restore` rejects a pre-donor checkpoint under the changed binding. The only existing config-rebind exception is the GX policy, whose `gx_rule_rebind` also rejects donor changes. The native checkpoint regression demonstrates refusal under the new binding and successful restore under the unchanged binding with an attached frozen donor. Extending that identity/rebind policy changes resume legality, so this lane stops S1 at the requested boundary. The existing `r1_handover.compare_configs` allows adding a pinned donor at an independently admitted initialization boundary; it does not authorize an in-place resume or bypass preparation.

## Source loading and real-weight command (S2/S3)

Rank zero attaches with `verify_assets=True` and authenticates the source heads. After the trainer's existing startup agreement, follower ranks attach with `verify_assets=False`, preserving `r1_persisted` relocation. The source artifact, feature contract, tensor content and visual identity checks remain enforced. Heads use memory mapping; ranks still construct their private frozen modules, so this does not claim zero per-rank loading or production throughput. The source must stay immutable on local storage throughout launch.

`N_DONOR_BINDING` must name a pinned JSON object with a top-level `scale_donor` key: `{"scale_donor": { ...the exact fields above... }}`. Set `PYTHON` to the environment's interpreter; the command has no hard-coded Trinity interpreter path. Real step-400 heads remain MISSING at `/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt` (SHA256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`). Step-544 heads have no supplied location, and the production FoV/source decision remains MISSING.
'''
(O/'READER_REQUEST.md').write_text(s)
inputs={str(p):sha(p),str(Path(__file__).resolve()):sha(__file__)}
for n in names:
 for root in (W/'work/base',T):
  p=root/'student_pilot'/n
  if p.exists():inputs[str(p)]=sha(p)
(O/'READER_SOURCE_HASHES.json').write_text(json.dumps(dict(input_sha256=inputs,files=[dict(path='student_pilot/'+n,base_sha256=sha(W/'work/base/student_pilot'/n) if (W/'work/base/student_pilot'/n).exists() else None,patched_sha256=sha(T/'student_pilot'/n)) for n in names],command='python code/reader_docs.py'),indent=2)+'\n')
