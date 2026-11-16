# Operator run sheet

**Production authority is still required.** ORCH accepted the seven sealed trainer-tree names at 1601Z. The CPU-fixture blocker is closed; each launch still needs a review bound to the current FAMILY, its candidate closure/export and exact ORCH GO (`RELEASE_BLOCKERS.json`). The delivered family keeps its release gate closed pending that authority.

All commands below are operator commands; none ran during this build. The wrapper path comes from the reviewed launcher (`/scratch/jjyeung/orch_n30/b01_d0guard/work/from13/readk/kit/launcher/orchard_launcher.py:24). Its installed behavior and current credentials were not checked.

Prepare the local environment:
```sh
set -euo pipefail
cd /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf" TRITON_CACHE_DIR="$PWD/work/cache/triton"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
```

Choose the step and its unused token from `OPERATOR_TOKENS.json`. Each token has its own plan, payload, input closure and return directory:

| Step | Token |
|---|---|
| 200 | `d8fa5baf8ed9478b` |
| 400 | `a15ae9c8dde0a119` |
| 600 | `979af7e386ece59d` |
| 800 | `c48905f32fb4fda9` |
| 1000 | `0bdc0b75d4b9bef3` |

Every fetch and packet upload uses `out/operator/governed_transfer.py`. It starts a stable Python root in state T before payload IO, waits for the limiter comm `ratelimit`, and calls:
```sh
/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane LANE --pid ROOT_PID --member-pid RL_PID --rl-pid RL_PID --expected-bytes BYTES --tier 3 --kind copy --nominal-mbps 8 --io-weight 1 --allow-resume
```
The root never execs another program. Only the governor resumes it; both producer and remote consumer wait for their lane to say `running` in `STATE.md`. The limiter starts with `ratelimit.py -q -L 1000 -B 65536`. The wrapper renames its record to `.done.<epoch>` after all pipeline processes finish, including on a nonzero exit. A failure never retries. Each call creates its own registration. These transfers cross the head node and write local scratch or Orchard, so they use `--io-weight 1` without `--writes-nfs`. An explicit `/home` or `/data*` output requires `writes_nfs: true`, which adds `--writes-nfs`.

The node must already have a live governor agent and installed helpers. The protocol is defined in `/data3/jjyeung/orch_n13_20261026/io_governor/README.md`. No governor, network or SSH command ran during this build.

Define the operator transfer function. It writes a small job description on scratch and launches one registered stream synchronously. The byte argument is the known size or a conservative positive upper bound; it does not grant extra bandwidth.
```sh
governed_transfer() {
  lane="$1"; bytes="$2"; output="$3"; producer="$4"; consumer="$5"
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$lane" "$bytes" "$output" "$producer" "$consumer" <<'PYJOB'
import json,sys
from pathlib import Path
lane,count,output,producer,consumer=sys.argv[1:]
job=dict(lane=lane,expected_bytes=int(count),producer=json.loads(producer))
if output: job['output']=str(Path(output).resolve())
else: job['consumer']=json.loads(consumer)
p=Path('work/transfers');p.mkdir(exist_ok=True)
with (p/(lane+'.json')).open('x') as stream: json.dump(job,stream)
PYJOB
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/operator/governed_transfer.py --job "work/transfers/$lane.json"
}
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
```

Fetch the selected closure with one read-only tar. The archive contains the artifact for that step even if tensor export publication is still pending. The separate completion record is required before plan preparation:
```sh
STEP=200; TOKEN=d8fa5baf8ed9478b
mkdir -p "work/fetch/$TOKEN"
governed_transfer "g4_${TOKEN}_closure" 20000000 "work/fetch/$TOKEN/closure.tar" "[\"bash\",\"$OSSH\",\"cd /project/community/jjyeung/okh7/x_f5c353f7 && tar --hard-dereference -cf - runs/359fcc3c/inputs runs/359fcc3c/m${STEP}/artifact.json runs/359fcc3c/binding.json k/d6827df0.json k/7.json k/routes.json k/benchmark_scene_exclusions.json k/dev_scene_exclusions.json\"]" ''
sha256sum "work/fetch/$TOKEN/closure.tar"
governed_transfer "g4_${TOKEN}_done" 65536 "work/fetch/$TOKEN/candidate.done" "[\"bash\",\"$OSSH\",\"cat /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m${STEP}.done\"]" ''
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/pack_candidate.py --source "work/fetch/$TOKEN/closure.tar" --step "$STEP" --out "out/closures/$TOKEN"
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/guard_kit/packet.py prepare --family out/FAMILY.json --done "work/fetch/$TOKEN/candidate.done" --step "$STEP" --metadata "out/closures/$TOKEN/CLOSURE.json" --token "$TOKEN" --out "out/plans/$TOKEN"
```

Run the same commands with each step/token pair. `CLOSURE.json` records both fetched-archive and neutral metadata-object digests. `CONFIG.json` pins them and the exact `.done` bytes. A foreign step or changed export is refused (`guard_kit/closure.py`, `guard_kit/packet.py`).

The independent reviewer supplies a JSON record with `verdict: "ACCEPT"`, a nonempty `reviewer`, and the exact `family_sha256`. ORCH supplies one exact line in `ORDER.md`, generated from the prepared plan without granting authority:
```sh
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import json,sys;from pathlib import Path;sys.path.insert(0,"out/guard_kit");from packet import order_line;print(order_line(json.loads(Path(sys.argv[1]).read_text())))' "out/plans/$TOKEN/CONFIG.json"
# Expected form: ORCH GO a15_cot_ap<TOKEN> <STEP> <PLAN_SHA256>
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/guard_kit/packet.py packet --config "out/plans/$TOKEN/CONFIG.json" --review REVIEW.json --order ORDER.md --out "out/packets/$TOKEN"
```

After the blockers are resolved, the packet builder emits `BATCH.sh`, `CONFIG.json`, `FAMILY.json`, `PACKET.json`, and the regular-file archives `p.tar` and `m.tar`. No new cloud object generation is needed for these packet inputs: they travel as pinned neutral Orchard files. Existing shared GCS assets retain their accepted generation pins (`inputs/BASELINE_CONFIG.json`).

Create the bounded return pool, copy the packet as one governed archive, and submit with all resources on the command line:
```sh
bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "mkdir -p /project/community/jjyeung/okh7/a936d80c /project/community/jjyeung/okh7/8c9d2e74/$TOKEN"
tar --hard-dereference -cf "work/fetch/$TOKEN/packet.tar" -C "out/packets/$TOKEN" BATCH.sh CONFIG.json FAMILY.json PACKET.json p.tar m.tar
PACKET_BYTES=$(stat -c %s "work/fetch/$TOKEN/packet.tar")
governed_transfer "g4_${TOKEN}_packet" "$PACKET_BYTES" '' "[\"cat\",\"$PWD/work/fetch/$TOKEN/packet.tar\"]" "[\"bash\",\"$OSSH\",\"tar xf - -C /project/community/jjyeung/okh7/8c9d2e74/$TOKEN\"]"
bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "sbatch --parsable --account=mt01 --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --signal=B:USR1@300 --no-requeue --chdir=/tmp --job-name=a15_cot_ap$TOKEN /project/community/jjyeung/okh7/8c9d2e74/$TOKEN/BATCH.sh"
```

The batch hashes `p.tar` before executing code and hashes `m.tar` before candidate staging. Both archives reject hard links. Any unexpected termination requires operator review; these commands contain no retry or requeue loop.

Fetch each return object through its own governor registration:
```sh
mkdir -p "out/fetched/$TOKEN"
governed_transfer "g4_${TOKEN}_exit" 65536 "out/fetched/$TOKEN/EXIT.json" "[\"bash\",\"$OSSH\",\"cat /project/community/jjyeung/okh7/a936d80c/$TOKEN/EXIT.json\"]" ''
governed_transfer "g4_${TOKEN}_return" 300000000 "out/fetched/$TOKEN/result.tar.gz" "[\"bash\",\"$OSSH\",\"cat /project/community/jjyeung/okh7/a936d80c/$TOKEN/result.tar.gz\"]" ''
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/guard_kit/fetch.py --config "out/plans/$TOKEN/CONFIG.json" --receipt "out/fetched/$TOKEN/EXIT.json" --archive "out/fetched/$TOKEN/result.tar.gz" --out "out/fetched/$TOKEN/x"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import hashlib;from pathlib import Path;assert hashlib.sha256(Path("../report/guard_read.py").read_bytes()).hexdigest()=="5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11"'
CANDIDATE_ARTIFACT=$(/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["artifact_sha256"])' "out/plans/$TOKEN/CONFIG.json")
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/report/guard_read.py --candidate "out/fetched/$TOKEN/x/R1.json" --candidate-artifact "$CANDIDATE_ARTIFACT" --step544 /scratch/jjyeung/orch_n30/b01_d0guard/work/ret544/native/R1.json --out "out/fetched/$TOKEN/report"
```

The cloud copy is `gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/<TOKEN>/result.tar.gz`; `EXIT.json` binds its bytes to the prepared plan. Early proof and canary receipts use the same pool/token and cloud prefix. A failed or synthetic return is not an empirical read.

Append the ledger record only after an actual successful submission, using the real job identifier:
```json
{"utc":"<UTC>","job":"<actual job>","job_name":"a15_cot_ap<TOKEN>","token":"<TOKEN>","run":"359fcc3c","step":"<STEP>","done_object":"<CONFIG.done.object>","done_bytes":"<CONFIG.done.bytes>","done_sha256":"<CONFIG.done.sha256>","closure_sha256":"<CONFIG.closure_source_sha256>","metadata_sha256":"<CONFIG.closure_archive_sha256>","family_sha256":"<CONFIG.family.sha256>","plan_sha256":"<CONFIG.plan_sha256>","status":"SUBMITTED"}
```

Ledger destination: `work/ORCHARD_LEDGER.jsonl`. No ledger row was written during this build.

The seven sealed trainer-tree names are ACCEPTED by ORCH 1601Z; no optional asset-copy migration is required by this run sheet. Existing production asset pins remain unchanged.

Report source SHA256: `5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11`. This is the intentional operator-supplied post-review change (`REPORT_PIN_G4.json`). Every production report supplies `CONFIG.artifact_sha256`; only recorded self-pair fixtures may use `--self-pair`.
