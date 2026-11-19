from pathlib import Path
W=Path(__file__).resolve().parents[1]
p=W/'work/new/tests/test_scale_donor.py';s=p.read_text()
a=s.index('    def test_mdg_runtime_strict_load_requires_reader_metadata_steps(')
b=s.index('    def test_pre_donor_resume_binding_stays_fail_closed(',a)
s=s[:a]+(W/'code/runtime_test.txt').read_text()+s[b:];p.write_text(s)
p=W/'out/READER_REQUEST.md';s=p.read_text()
s=s.replace('The separate runtime loader needs the metadata steps below before its strict head load. Keep the existing private visual copy frozen.', 'The separate runtime loader must first restore `depth.model.visual.*` from the export heads with `strict=True`, then freeze that visual with `requires_grad_(False)`, then attach the donor and perform the metadata and strict-load steps below. Its base-weight load does not restore the private visual, and it does not read `depth_init`.')
s=s.replace('Run `PYTHON=/path/to/python bash out/REAL_WEIGHT_COMMAND.sh`', 'Run `PYTHON=/path/to/python bash /absolute/path/to/donor3/out/REAL_WEIGHT_COMMAND.sh`')
s=s.replace('SHA256 in PATCH_DONOR2', 'SHA256 in PATCH_DONOR3')
a=s.index('## Separate runtime strict-load sequence')
b=s.index('## Preparation and checkpoint boundary', a)
s=s[:a]+'''## Separate runtime load sequence (M3/M4)

After the runtime constructs `CarrierC1` and `full_ft.load_export` restores the base tensors, execute the following block in place of its head load. `binding` is the authenticated `scale_donor` configuration; `artifact` and `heads_path` come from the authenticated export. Preserve the existing bundle authentication and relocation scope.

```python
from student_pilot import scale_donor

heads = torch.load(heads_path, map_location="cpu", weights_only=True)
visual = model.auxiliary_heads.depth.model.visual
prefix = "depth.model.visual."
visual.load_state_dict({key[len(prefix):]: value for key, value in heads.items()
                        if key.startswith(prefix)}, strict=True)
visual.requires_grad_(False)
scale_donor.attach(model, binding)
metadata = heads.pop("_scale_donor", None)
if metadata != artifact.get("scale_donor"):
    raise ValueError("Scale donor artifact/head metadata differs")
scale_donor.verify_export(model, heads, metadata)
model.auxiliary_heads.load_state_dict(heads, strict=True)
```

Only keys starting with the exact prefix `depth.model.visual.` enter the visual load; strip that prefix and require complete, strict coverage. Keep those keys in `heads` for the final strict load. The private visual starts as a trainable deep copy of the empty base. Loading base tensors alone does not initialize it, and the standalone runtime skips `depth_init`. Restore the visual and freeze it before attaching: `attach` still authenticates it against `binding['visual_sha256']`. A changed visual must fail at attach. `_scale_donor` is metadata and must be removed, compared with `artifact['scale_donor']`, and verified before the full strict head load.

`test_mdg_runtime_strict_load_requires_reader_metadata_steps` executes a test adapter inserted at the strict-load site of the actual `mdg_runtime.load_runtime` function body. The runtime constructs the real `CarrierC1` on a differently initialized tiny Qwen base and calls the real `full_ft.load_export`; the test never substitutes `CarrierC1` or supplies an already attached model. It loads a native fixture export after two optimizer steps and checks every exported head tensor for byte identity. Negative cases reject the old attach-first order, freezing alone, loading without freezing, a tampered or incomplete visual, unpopped metadata, inconsistent metadata, and a changed donor tensor.

The test substitutes bundle authentication, processor/token setup and the tiny empty-base boundary, and isolates `r2_policy.unsupported_entry`. It checks the proposed reader sequence; it does not install it in the shipped runtime, validate a production bundle, or run real pretrained weights. Production still requires an authenticated R2 reader adapter. The legacy-reader guard remains enabled.

'''+s[b:]
p.write_text(s)
p=W/'out/REAL_WEIGHT_COMMAND.sh';s=p.read_text().replace('bash out/REAL_WEIGHT_COMMAND.sh','bash /absolute/path/to/donor3/out/REAL_WEIGHT_COMMAND.sh');p.write_text(s)
(W/'STATUS.md').write_text('The recipe restores all depth.model.visual.* tensors strictly and freezes the private visual before donor attachment. The runtime regression now constructs real CarrierC1 and uses real base export loading; it checks the documented sequence and eight negative cases. Donor training sources remain byte-identical to donor2. Validation is running.\n')
