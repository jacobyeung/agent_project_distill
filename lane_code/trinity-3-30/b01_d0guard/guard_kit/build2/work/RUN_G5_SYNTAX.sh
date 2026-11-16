set -euo pipefail
cd /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf" TRITON_CACHE_DIR="$PWD/work/cache/triton"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

/usr/bin/python3 -s /scratch/jjyeung/io_governor/register.py --lane LANE --pid ROOT_PID --member-pid RL_PID --rl-pid RL_PID --expected-bytes BYTES --tier 3 --kind copy --nominal-mbps 8 --io-weight 1 --allow-resume

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

STEP=200; TOKEN=d8fa5baf8ed9478b
mkdir -p "work/fetch/$TOKEN"
governed_transfer "g4_${TOKEN}_closure" 20000000 "work/fetch/$TOKEN/closure.tar" "[\"bash\",\"$OSSH\",\"cd /project/community/jjyeung/okh7/x_f5c353f7 && tar --hard-dereference -cf - runs/359fcc3c/inputs runs/359fcc3c/m${STEP}/artifact.json runs/359fcc3c/binding.json k/d6827df0.json k/7.json k/routes.json k/benchmark_scene_exclusions.json k/dev_scene_exclusions.json\"]" ''
sha256sum "work/fetch/$TOKEN/closure.tar"
governed_transfer "g4_${TOKEN}_done" 65536 "work/fetch/$TOKEN/candidate.done" "[\"bash\",\"$OSSH\",\"cat /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m${STEP}.done\"]" ''
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/pack_candidate.py --source "work/fetch/$TOKEN/closure.tar" --step "$STEP" --out "out/closures/$TOKEN"
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/guard_kit/packet.py prepare --family out/FAMILY.json --done "work/fetch/$TOKEN/candidate.done" --step "$STEP" --metadata "out/closures/$TOKEN/CLOSURE.json" --token "$TOKEN" --out "out/plans/$TOKEN"

/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import json,sys;from pathlib import Path;sys.path.insert(0,"out/guard_kit");from packet import order_line;print(order_line(json.loads(Path(sys.argv[1]).read_text())))' "out/plans/$TOKEN/CONFIG.json"
# Expected form: ORCH GO a15_cot_ap<TOKEN> <STEP> <PLAN_SHA256>
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/guard_kit/packet.py packet --config "out/plans/$TOKEN/CONFIG.json" --review REVIEW.json --order ORDER.md --out "out/packets/$TOKEN"

bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "mkdir -p /project/community/jjyeung/okh7/a936d80c /project/community/jjyeung/okh7/8c9d2e74/$TOKEN"
tar --hard-dereference -cf "work/fetch/$TOKEN/packet.tar" -C "out/packets/$TOKEN" BATCH.sh CONFIG.json FAMILY.json PACKET.json p.tar m.tar
PACKET_BYTES=$(stat -c %s "work/fetch/$TOKEN/packet.tar")
governed_transfer "g4_${TOKEN}_packet" "$PACKET_BYTES" '' "[\"cat\",\"$PWD/work/fetch/$TOKEN/packet.tar\"]" "[\"bash\",\"$OSSH\",\"tar xf - -C /project/community/jjyeung/okh7/8c9d2e74/$TOKEN\"]"
bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "sbatch --parsable --account=mt01 --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --signal=B:USR1@300 --no-requeue --chdir=/tmp --job-name=a15_cot_ap$TOKEN /project/community/jjyeung/okh7/8c9d2e74/$TOKEN/BATCH.sh"

mkdir -p "out/fetched/$TOKEN"
governed_transfer "g4_${TOKEN}_exit" 65536 "out/fetched/$TOKEN/EXIT.json" "[\"bash\",\"$OSSH\",\"cat /project/community/jjyeung/okh7/a936d80c/$TOKEN/EXIT.json\"]" ''
governed_transfer "g4_${TOKEN}_return" 300000000 "out/fetched/$TOKEN/result.tar.gz" "[\"bash\",\"$OSSH\",\"cat /project/community/jjyeung/okh7/a936d80c/$TOKEN/result.tar.gz\"]" ''
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/guard_kit/fetch.py --config "out/plans/$TOKEN/CONFIG.json" --receipt "out/fetched/$TOKEN/EXIT.json" --archive "out/fetched/$TOKEN/result.tar.gz" --out "out/fetched/$TOKEN/x"
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import hashlib;from pathlib import Path;assert hashlib.sha256(Path("../report/guard_read.py").read_bytes()).hexdigest()=="5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11"'
CANDIDATE_ARTIFACT=$(/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["artifact_sha256"])' "out/plans/$TOKEN/CONFIG.json")
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/report/guard_read.py --candidate "out/fetched/$TOKEN/x/R1.json" --candidate-artifact "$CANDIDATE_ARTIFACT" --step544 /scratch/jjyeung/orch_n30/b01_d0guard/work/ret544/native/R1.json --out "out/fetched/$TOKEN/report"
