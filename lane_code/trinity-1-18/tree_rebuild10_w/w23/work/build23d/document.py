from pathlib import Path
import ast,datetime,difflib,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23d';A=L/'attic/build23d';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
kit=J.load(D/'KIT.json');guard=(K/'b/g.py').read_text()
target=L.parent/'w24/work/build21/kit.py';baseline=target.read_text()
tree=ast.parse(baseline)
old=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and "raise RuntimeError('E42')" in n.value)
assert baseline.count(old)==1
patched=baseline.replace(old,guard).replace('minimum_gpu_gib=80','minimum_gpu_gib=75')
assert guard in [n.value for n in ast.walk(ast.parse(patched)) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
assert 'minimum_gpu_gib=75' in patched
delta=''.join(difflib.unified_diff(baseline.splitlines(True),patched.splitlines(True),fromfile='a/work/build21/kit.py',tofile='b/work/build21/kit.py'))
J.write(D/'BUILD24_PATCH_CHECK.json',dict(status='PASS',target=str(target),read_only=True,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=hashlib.sha256(baseline.encode()).hexdigest(),patched_sha256=hashlib.sha256(patched.encode()).hexdigest(),patch_matches=True))
for name in ('GUARD_PATCH.md','GUARD_PATCH.diff'):(L/'out'/name).rename(A/name)
(L/'out/GUARD_PATCH.diff').write_text(delta)
text='''The GPU guard prints one flushed JSON diagnostic and refuses with `RuntimeError('E42')` if any diagnostic read raises. Admission requires available CUDA, at least one device, known memory, and at least `75*(1<<30)` bytes. The guard does not print `CUDA_VISIBLE_DEVICES` contents. It prints a device name only when the entire name matches `^[A-Za-z0-9 ._-]{1,64}$`; otherwise it prints `"?"`.

Apply to build 24's `w24/work/build21/kit.py`, or the equivalent generator:

1. Replace only the Python payload in `(K/'b/g.py').write_text(...)` with the exact code below. Set resource metadata `minimum_gpu_gib=75`.
2. Emit `q/b/g.py` from that literal. Keep build 24's authenticated source archive, config and resolver unchanged. `work/build23d/patch.py` demonstrates extraction with AST; its workspace-specific upload bookkeeping is not a build-24 generator.
3. Set decoded `q/BUILD.json.resource_request.minimum_gpu_gib=75`. Recompute `q/SHA256SUMS.txt` over all kit files except `BUILD.json` and `SHA256SUMS.txt`, sorted by relative path, as `<sha256>  <path>\\n`. Set decoded `BUILD.json.kit_sha256` to that file's SHA-256 and re-encode with the existing `capsule_json` helper. Preserve the source seal and `GO=false`.
4. Refresh upload names, sizes, hashes and kit seal metadata. Retain superseded files under build 24's attic.
5. Run the guard, decoded-scanner, kit, naming and resolver tests. Adapt only workspace paths and diagnostic-schema expectations in inherited tests. Verify the source, config and resolver bytes remain unchanged.

`GUARD_PATCH.diff` contains the two generator hunks against the read-only build-24 source. `work/build23d/BUILD24_PATCH_CHECK.json` records its exact source hash and successful in-memory patch validation. If that generator already has a different guard, replace its guard payload directly with the code below; preserve all unrelated edits.

```python
'''+guard+'''```

Diagnostic keys: `v` is the torch version; `a` is CUDA availability; `c` is the device count; `e` states whether `CUDA_VISIBLE_DEVICES` is set; `ec` counts comma-separated entries, with zero for an unset or empty value (empty entries within a nonempty value count). `n` is the validated device name; `m` is total memory in bytes; `d0` and `dc` state whether `/dev/nvidia0` and `/dev/nvidiactl` exist; `x` records any diagnostic-read exception. Reads and conversions run inside the exception handler. Unread values retain safe defaults. The raw environment value and exception text are never emitted. Device-node existence remains diagnostic only.

The guard runs inside the existing bwrap view. Its NVIDIA device and driver-library binds remain unchanged; the code audit is in `work/build23d/VIEW_AUDIT.json`.

The two reviewer cases fail on the sealed build-23c guard and pass on this guard (`work/build23d/REVIEWER_BEFORE.json`, `REVIEWER_AFTER.json`): a missing torch version produces a diagnostic plus E42, and the private environment value is absent from both raw output and the real `screen()` output. The inherited nine guard cases remain passing (`LEGACY_GUARD_TESTS.json`); read-failure, import-failure, environment-count and name-boundary cases are in `GUARD_TESTS.json`.
'''
(L/'out/GUARD_PATCH.md').write_text(text)
p=B/'OPERATOR.md';s=p.read_text();p.rename(A/'OPERATOR.md')
s=s.replace(J.load(D/'START.json')['kit']['SHA256SUMS.txt'],kit['kit_seal'])
old='The in-view GPU guard accepts at least 75 GiB and prints one opaque-key JSON diagnostic before deciding.'
start=s.index(old)
s=s[:start]+'''The in-view GPU guard accepts at least 75 GiB and prints one opaque-key JSON diagnostic before deciding. Any diagnostic-read exception prints the available safe fields and refuses E42. CUDA_VISIBLE_DEVICES contributes only a set flag and comma-entry count; the device name must match the documented 64-character ASCII allowlist. Keys and build-24 application instructions are in `../../out/GUARD_PATCH.md`; upload the three files in `../../out/UPLOADS_NEW_23D.json`. NVIDIA binds are unchanged. Production GO remains false.
'''
# Refresh the inventory total without changing other operator instructions.
import re
u=J.load(B/'UPLOADS.json')
s=re.sub(r'Upload total: \d+ bytes in \d+ files',f"Upload total: {u['total_bytes']} bytes in {len(u['files'])} files",s)
p.write_text(s)
print('Build-24 patch verified in memory; operator metadata refreshed.')
