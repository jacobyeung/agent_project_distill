from pathlib import Path
import json
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';p=O/'kit_parity50/README.md';s=p.read_text()
s=s.replace('The gate defaults to **step 400**','The kit binds **step 400 only**')
start=s.index('`BOUND_EXPORT` selects');end=s.index('```bash',start)
s=s[:start]+'''`a19 build` checks the reviewed step-400 identity and preparation hashes before reading or copying the base. No other export can authorize adoption. A fresh package token identifies the ON build; it does not reuse the source package's token.

'''+s[end:]
s=s.replace('BOUND_EXPORT=${BOUND_EXPORT:-"$DELIVERY/operations/BOUND_EXPORT.json"}\n','').replace('EXPORT_BINDING=${EXPORT_BINDING:-"$DELIVERY/operations/binding.default.json"}','EXPORT_BINDING="$DELIVERY/operations/binding.default.json"')
start=s.index('For a different target,');end=s.index('`adopted` retains',start);s=s[:start]+s[end:]
s=s.replace('It dereferences symlinks and records','It refuses any symlink whose resolved target leaves `logical/d` (including directory links, chains, dangling links and cycles), preserves admitted links with `tar -cf - -C <logical>/d .`, and records')
s=s.replace('A tar failure leaves no successful CPU.json and is not retried.','Validation and tar run in the same live namespace. Tar stderr goes to `results/4.err`. A tar failure leaves no successful CPU.json and is not retried.')
s=s.replace('restore, artifact-binding, manifest and export-pin receipts.','restore, artifact-binding, manifest, export-pin and ENVIRONMENT.json receipts. ON prepare adds the compiled CUDA version to ENVIRONMENT.json and its SHA256 to READY.')
s=s.replace('manifest.json EXPORT_PIN.json 1.json','manifest.json EXPORT_PIN.json 1.json ENVIRONMENT.json')
s=s.replace('The selected export defaults to the pinned step-400 export; `--bound-export` explicitly changes it.','The complete export must equal the supplied step-400 pin. The gate also authenticates ENVIRONMENT.json against CPU READY; submit compares its hash and torch/transformers/CUDA versions with ue.json.')
s=s.replace('Reserve storage for the archive before running `o_cpu.sh`. Its size is recorded by the job; no production archive size was measured here.','Reserve storage for the archive before running `o_cpu.sh`: **about 33 GB, estimated**, from about 32.6 GB of expanded inputs plus tar headers. Preserving symlinks avoids duplicated shards and heads. Reserve separate space for extraction, sources and runtime outputs. The job records actual bytes; no production archive size was measured here.')
s=s.replace('salloc --account=mt01','GATE_TOKEN=$(/usr/bin/python3 -I -s -B -c \'import secrets;print(secrets.token_hex(6))\')\nsalloc --account=mt01')
s=s.replace('--job-name=ab0123456789','--job-name="a15_cot_ap${GATE_TOKEN}"')
s=s.replace("assert asset['path']==str(p/'a/4.tar') and archive.stat().st_size==asset['bytes']", "assert Path(asset['path']).resolve()==(p/'a/4.tar').resolve() and archive.stat().st_size==asset['bytes']")
s=s.replace('cp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"','ln -s binding.json "$GPU_LOGICAL/d/7.json"\ntest ! -e "$GPU_LOGICAL/d/9.json"\nln -s ENVIRONMENT.json "$GPU_LOGICAL/d/9.json"')
s=s.replace('The last file is a byte-identical neutral alias for the CPU binding.','Set `environment_receipt=$GPU_LOGICAL/d/9.json`. The neutral binding and environment aliases must be symlinks, as created above.')
s=s.replace('map the other private prepared asset paths to staged opaque aliases of those same files.','map the other private prepared asset paths to staged opaque aliases of those same files. These aliases must be symlinks so `resolve()` reaches the manifest allow-list target; copies are rejected.')
s=s.replace('--asset-receipts "$LOCAL/adopted/proof" --bound-export "$BOUND_EXPORT" \\', '--asset-receipts "$LOCAL/adopted/proof" \\')
needle='nice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py'
new='''# BEGIN GPU_ENVIRONMENT
: "${GPU_LOGICAL:?Exact logical root extracted above}"
GPU_KIT=/scratch/jjyeung/ab0123456789
READ_PYTHON="$GPU_LOGICAL/d/v/py"
export XDG_CACHE_HOME="$GPU_KIT/u6" HF_HOME="$GPU_KIT/u6/u0" TRITON_CACHE_DIR="$GPU_KIT/u6/u1"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
mkdir -p "$XDG_CACHE_HOME" "$HF_HOME" "$TRITON_CACHE_DIR"
nice -n 10 "$READ_PYTHON" -I -s -B - "$GPU_LOGICAL/d/ENVIRONMENT.json" <<'PYENV'
import json,sys,torch,transformers
from pathlib import Path
torch.set_num_threads(8)
environment=json.loads(Path(sys.argv[1]).read_text())
actual=dict(torch=torch.__version__,transformers=transformers.__version__,cuda=torch.version.cuda)
expected=dict(torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])
if actual!=expected or not actual['cuda'] or not torch.cuda.is_available():
    raise ValueError('GPU interpreter/environment preflight failed')
print('Environment preflight passed')
PYENV
# END GPU_ENVIRONMENT
'''+needle
assert needle in s;s=s.replace(needle,new)
s=s.replace('Every arm starts a fresh process.','The preflight runs the archived production interpreter outside bwrap and fails before the gate if it cannot start, lacks dependencies/CUDA, or differs from ENVIRONMENT.json. No substitute interpreter is accepted. The gate parent, every worker and receipt writer independently compare the recorded versions and SHA256. Cache roots are explicit under the opaque kit root, matching A4\'s XDG/HF pattern with an explicit Triton root.\n\nEvery arm starts a fresh process.')
s=s.replace('Each RUN.json records the adopted package plan','Each RUN.json and ue.json record the checked torch/transformers/CUDA versions and ENVIRONMENT.json SHA256. Each RUN.json also records the adopted package plan')
s=s.replace('| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |','| 5. Decision export | Bind only the supplied step-400 export at build and gate. | Other identities refuse before the builder reads the base; wrong artifact refuses at the gate. |')
s+='''
## Review round 8: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| 1. Archive breaks loader admission | Preserve in-tree symlinks; refuse escaping targets before tar; estimated archive is about 33 GB. | Extract an absolute heads link and run real Artifact.verify/load_native admission; reject external, chained, directory, dangling and cyclic links. |
| 2. Environment unspecified | Use archived d/v/py; preflight versions/CUDA; pin ENVIRONMENT.json through READY, gate and submit; set opaque cache roots. | Changed versions/hash and CPU build refuse; synthetic matching versions pass; submit rejects each changed field. |
| 3. Other export checked late | Builder admits only reviewed step-400 identity/preparation. | Eleven identity/preparation mutations refuse before reading the base. |
| 4. Unresolved package path | Resolve both archive-path operands. | README validation executes through a symlinked package parent. |
| 5. Handoff details | Aliases are symlinks; retain tar stderr; generate a fresh a15_cot_ap job token. | Error text survives; commands and alias instructions are checked. |
'''
p.write_text(s)
p=O/'kit_parity50/config.example.json';v=json.loads(p.read_text());v['environment_receipt']='/scratch/jjyeung/b01ec87a6f29b/d/9.json';p.write_text(json.dumps(v,indent=2)+'\n')
print('README binds step 400 only, preserves aliases, defines GPU environment, resolves archive paths and labels archive estimate.')
