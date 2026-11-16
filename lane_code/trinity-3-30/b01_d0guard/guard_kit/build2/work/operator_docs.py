from pathlib import Path
import json,secrets,sys,shlex
B=Path(__file__).resolve().parents[1];O=B/'out';W=B.parents[1]/'work'
sys.path.insert(0,str(O/'guard_kit'));from guard_core import read,write,sha
steps=(200,400,600,800,1000)
tokens={str(s):secrets.token_hex(8) for s in steps}
write(O/'OPERATOR_TOKENS.json',tokens)
PYTHON='/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B'
OSSH='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh'
lines=['# Operator run sheet','',
 '**Release is blocked.** The code can emit a packet under complete fixture authority (`PACKET_TEST.json`), but the delivered family refuses production launch (`RELEASE_BLOCKERS.json`). Finish the runtime naming migration, validate the whole-worker path, regenerate the family, and obtain independent review before using the launch commands. Do not enable release by changing a boolean alone.',
 '', 'All commands below are operator commands; none ran during this build. The wrapper path comes from the reviewed launcher (`'+str(W/'from13/readk/kit/launcher/orchard_launcher.py')+':24). Its installed behavior and current credentials were not checked.',
 '', 'Prepare the local environment:', '```sh','cd '+str(B),
 'export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1',
 'export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf" TRITON_CACHE_DIR="$PWD/work/cache/triton"',
 'export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1','```','',
 'Choose the step and its unused token from `OPERATOR_TOKENS.json`. Each token has its own plan, payload, input closure and return directory:', '',
 '| Step | Token |','|---|---|']
for step in steps:lines.append(f'| {step} | `{tokens[str(step)]}` |')
lines+=['','Fetch the selected closure with one read-only small tar. The archive contains the artifact for that step even if tensor export publication is still pending. The separate completion record is required before plan preparation:', '```sh',
 f'STEP=200; TOKEN={tokens["200"]}',
 'mkdir -p "work/fetch/$TOKEN"',
 'bash '+OSSH+' "cd /project/community/jjyeung/okh7/x_f5c353f7 && tar --hard-dereference -cf - runs/359fcc3c/inputs runs/359fcc3c/m${STEP}/artifact.json runs/359fcc3c/binding.json k/d6827df0.json k/7.json k/routes.json k/benchmark_scene_exclusions.json k/dev_scene_exclusions.json" | pv -q -L 8m > "work/fetch/$TOKEN/closure.tar"',
 'sha256sum "work/fetch/$TOKEN/closure.tar"',
 'bash '+OSSH+' "cat /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m${STEP}.done" > "work/fetch/$TOKEN/candidate.done"',
 'nice -n 10 '+PYTHON+' work/pack_candidate.py --source "work/fetch/$TOKEN/closure.tar" --step "$STEP" --out "out/closures/$TOKEN"',
 'nice -n 10 '+PYTHON+' out/guard_kit/packet.py prepare --family out/FAMILY.json --done "work/fetch/$TOKEN/candidate.done" --step "$STEP" --metadata "out/closures/$TOKEN/CLOSURE.json" --token "$TOKEN" --out "out/plans/$TOKEN"','```','',
 'Run the same commands with each step/token pair. `CLOSURE.json` records both fetched-archive and neutral metadata-object digests. `CONFIG.json` pins them and the exact `.done` bytes. A foreign step or changed export is refused (`guard_kit/closure.py`, `guard_kit/packet.py`).',
 '', 'The independent reviewer supplies a JSON record with `verdict: "ACCEPT"`, a nonempty `reviewer`, and the exact `family_sha256`. ORCH supplies one exact line in `ORDER.md`, generated from the prepared plan without granting authority:',
 '```sh',PYTHON+' -c \'import json,sys;from pathlib import Path;sys.path.insert(0,"out/guard_kit");from packet import order_line;print(order_line(json.loads(Path(sys.argv[1]).read_text())))\' "out/plans/$TOKEN/CONFIG.json"',
 '# Expected form: ORCH GO a15_cot_ap<TOKEN> <STEP> <PLAN_SHA256>',
 'nice -n 10 '+PYTHON+' out/guard_kit/packet.py packet --config "out/plans/$TOKEN/CONFIG.json" --review REVIEW.json --order ORDER.md --out "out/packets/$TOKEN"','```','',
 'After the blockers are resolved, the packet builder emits `BATCH.sh`, `CONFIG.json`, `FAMILY.json`, `PACKET.json`, and the regular-file archives `p.tar` and `m.tar`. No new cloud object generation is needed for these packet inputs: they travel as pinned neutral Orchard files. Existing shared GCS assets retain their accepted generation pins (`inputs/BASELINE_CONFIG.json`).',
 '', 'Create the bounded return pool, copy the packet as one throttled archive, and submit with all resources on the command line:', '```sh',
 'bash '+OSSH+' "mkdir -p /project/community/jjyeung/okh7/a936d80c /project/community/jjyeung/okh7/8c9d2e74/$TOKEN"',
 'tar --hard-dereference -cf - -C "out/packets/$TOKEN" BATCH.sh CONFIG.json FAMILY.json PACKET.json p.tar m.tar | pv -q -L 8m | bash '+OSSH+' "tar xf - -C /project/community/jjyeung/okh7/8c9d2e74/$TOKEN"',
 'bash '+OSSH+' "sbatch --parsable --account=mt01 --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --signal=B:USR1@300 --no-requeue --chdir=/tmp --job-name=a15_cot_ap$TOKEN /project/community/jjyeung/okh7/8c9d2e74/$TOKEN/BATCH.sh"','```','',
 'The batch hashes `p.tar` before executing code and hashes `m.tar` before candidate staging. Both archives reject hard links. Any unexpected termination requires operator review; these commands contain no retry or requeue loop.',
 '', 'Fetch the return only after successful IO-governor registration. The registration script was unavailable during the build, so its installed CLI must be confirmed by the operator; the stream itself is explicit:', '```sh',
 PYTHON+' /data3/jjyeung/orch_n13_20261026/io_governor/register.py --tier 3 --allow-resume',
 '# Stop here if registration fails; use the governor-issued authorization for the stream below.',
 'mkdir -p "out/fetched/$TOKEN"',
 'bash '+OSSH+' "cat /project/community/jjyeung/okh7/a936d80c/$TOKEN/EXIT.json" > "out/fetched/$TOKEN/EXIT.json"',
 'bash '+OSSH+' "cat /project/community/jjyeung/okh7/a936d80c/$TOKEN/result.tar.gz" | pv -q -L 8m > "out/fetched/$TOKEN/result.tar.gz"',
 'nice -n 10 '+PYTHON+' out/guard_kit/fetch.py --config "out/plans/$TOKEN/CONFIG.json" --receipt "out/fetched/$TOKEN/EXIT.json" --archive "out/fetched/$TOKEN/result.tar.gz" --out "out/fetched/$TOKEN/x"',
 'nice -n 10 '+PYTHON+' '+str(B.parents[1]/'guard_kit/report/guard_read.py')+' --candidate "out/fetched/$TOKEN/x/R1.json" --step544 '+str(W/'ret544/native/R1.json')+' --out "out/fetched/$TOKEN/report"','```','',
 'The cloud copy is `gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/<TOKEN>/result.tar.gz`; `EXIT.json` binds its bytes to the prepared plan. Early proof and canary receipts use the same pool/token and cloud prefix. A failed or synthetic return is not an empirical read.',
 '', 'Append the ledger record only after an actual successful submission, using the real job identifier:', '```json',
 '{"utc":"<UTC>","job":"<actual job>","job_name":"a15_cot_ap<TOKEN>","token":"<TOKEN>","run":"359fcc3c","step":"<STEP>","done_object":"<CONFIG.done.object>","done_bytes":"<CONFIG.done.bytes>","done_sha256":"<CONFIG.done.sha256>","closure_sha256":"<CONFIG.closure_source_sha256>","metadata_sha256":"<CONFIG.closure_archive_sha256>","family_sha256":"<CONFIG.family.sha256>","plan_sha256":"<CONFIG.plan_sha256>","status":"SUBMITTED"}',
 '```','', 'Ledger destination: `work/ORCHARD_LEDGER.jsonl`. No ledger row was written during this build.',
 '', 'Operational asset copies with identical bytes can use the following neutral paths. These copies are not yet applied to every runtime dependency; they do not by themselves close the naming blocker:', '```sh','mkdir -p /project/community/jjyeung/okh7/8c9d2e74']
mapping=read(OLD/'OPERATIONAL_NAME_MAP.json') if (OLD:=B.parent/'build/out').joinpath('OPERATIONAL_NAME_MAP.json').exists() else {}
for old,new in mapping.items():lines+=['cp -- '+shlex.quote(old)+' '+shlex.quote(new),'sha256sum -- '+shlex.quote(old)+' '+shlex.quote(new)]
lines+=['```','', 'The source-copy commands run on Orchard. They were not executed or checked against live archives. The local build performs no network operation or submission.']
(O/'RUN.md').write_text('\n'.join(lines)+'\n')
