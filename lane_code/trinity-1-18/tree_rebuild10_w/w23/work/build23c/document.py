from pathlib import Path
import difflib,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build23c';B=L/'work/build21';A=L/'attic/build23c';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
kit=J.load(D/'KIT.json');guard=(K/'b/g.py').read_text()
delta=''.join(difflib.unified_diff((A/'kit.py').read_text().splitlines(True),(B/'kit.py').read_text().splitlines(True),fromfile='a/work/build21/kit.py',tofile='b/work/build21/kit.py'))
(L/'out/GUARD_PATCH.diff').write_text(delta)
text='''The kit guard accepts CUDA device 0 when CUDA is available, the device count is positive, its properties can be queried, and total memory is at least `75*(1<<30)` bytes (80,530,636,800 bytes). It prints one flushed JSON line before accepting or raising `RuntimeError('E42')`.

Apply to build 24 at `w24/work/build21/kit.py`, or the generator that writes `q/b/g.py`:

1. Locate `(K/'b/g.py').write_text(...)`. Replace only its triple-quoted Python payload with the exact code below. Keep the generator's existing output path and quoting.
2. Change the generator's resource metadata from `minimum_gpu_gib=80` to `minimum_gpu_gib=75` (or the equivalent dictionary value).
3. Regenerate `q/b/g.py` from that literal. For a kit-only repair, do not rerun a legacy whole-kit builder that replaces build 24's authenticated config or source archive. `work/build23c/patch.py` demonstrates AST extraction of the guard literal.
4. Update decoded `q/BUILD.json.resource_request.minimum_gpu_gib` to 75. Recompute `q/SHA256SUMS.txt` over all kit files except `BUILD.json` and `SHA256SUMS.txt`, sorted by relative name, with lines `<sha256>  <name>\\n`. Set decoded `BUILD.json.kit_sha256` to the SHA-256 of the checksum file, preserve the source seal and `GO=false`, and re-encode the capsule with the existing `capsule_json` helper. Update upload hashes, sizes and the kit seal in operator/delivery metadata.
5. Run `work/build23c/guard_tests.py` (adapt only its workspace paths), build 24's decoded scanner, kit/naming/resolver suites and its own-config look-ahead. Verify all source bytes, config, resolver and view shell remain unchanged. Retain superseded files in that workspace's attic.

The companion `GUARD_PATCH.diff` has exactly the two generator edits, using build 23b as context; apply those same hunks to the matching build-24 generator. Do not copy this kit's source/config files into build 24.

```python
'''+guard+'''```

Diagnostic keys: `v` = torch version; `a` = CUDA availability; `c` = device count; `e` = `CUDA_VISIBLE_DEVICES` (`null` if unset); `n` = device name; `m` = total memory in bytes; `d0` and `dc` = existence of `/dev/nvidia0` and `/dev/nvidiactl`; `x` = a CUDA query raised. Unavailable properties remain `null`. JSON encoding keeps values on one line. Device-node existence is diagnostic: CUDA's availability and properties decide admission.

The guard executes inside bwrap: `q/job.sh` invokes `b/x.py`/`bootstrap`, which runs decoded `k/j.json`; that shell constructs `BW` and invokes `"${BW[@]}" ... "$Q_KIT/b/g.py"`. P's `ext/pwrap/b/c.sh:339-366` and this view both bind all host `/dev` with `--dev-bind /dev /dev`. They preserve host top-level symlinks and read-only binds, including `/usr`, `/lib*`, `/opt`, and `/run`, through which host driver libraries remain visible. The kit's private `/tmp` restores `Q_ROOT` before later binds. No NVIDIA bind repair is needed. This code audit does not establish which devices or driver libraries were present in job 173076.

Regression evidence: 85,520,809,984 bytes refuses under the 80 GiB guard and passes under the 75 GiB guard; no CUDA and 70 GiB refuse under both. Exact-threshold, one-byte-below, zero-count, failed-property-query, and missing-node diagnostics are covered in `work/build23c/GUARD_TESTS.json`. The view audit is in `work/build23c/VIEW_AUDIT.json`. The requested comparison is retained as test evidence.
'''
(L/'out/GUARD_PATCH.md').write_text(text)
p=B/'OPERATOR.md';s=p.read_text();p.rename(A/'OPERATOR.md')
s=s.replace('67ce92f6f7e96af1bd706fe020cef0c989c947149b7327fdde92138d67268a6c',kit['kit_seal'])
s+='\nThe in-view GPU guard accepts at least 75 GiB and prints one opaque-key JSON diagnostic before deciding. It refuses missing CUDA or failed device queries with E42. Keys and build-24 application instructions are in `../../out/GUARD_PATCH.md`; upload the three changed files listed in `../../out/UPLOADS_NEW_23C.json`. The NVIDIA device and driver-library binds match P. Production GO remains false.\n'
p.write_text(s)
print('guard patch and operator metadata written')
