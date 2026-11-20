#!/bin/bash
# CPU-only sender job. Usage (sbatch): job.sh <idle_exit_seconds> [probe]. The key arrives only in the environment passed at submission.
set -u
J=/project/community/jjyeung/4f5e45fe5d74c
W=/tmp/nvo_${SLURM_JOB_ID}
mkdir -p $W
echo "host $(hostname) start $(date -u +%FT%TZ) job ${SLURM_JOB_ID}"
echo "egress $(curl -s -m 15 https://api.ipify.org || echo none) / $(curl -s -m 15 https://ifconfig.me || echo none)"
python3 -m pip install --quiet --disable-pip-version-check --no-cache-dir --target $W/site pillow==11.0.0 2>&1 | tail -3
export PYTHONPATH=$W/site
python3 -c "import PIL; print('PIL', PIL.__version__)" || exit 3
if [ "${2:-}" = probe ]; then
python3 - <<'PY'
import os, json, urllib.request, time
k = os.environ.get('NVK_A'); assert k, 'no key in env'
t = time.time(); req = urllib.request.Request('https://inference-api.nvidia.com/v1/models', headers={'Authorization': 'Bearer ' + k})
with urllib.request.urlopen(req, timeout=60) as r: d = json.loads(r.read()); print('models-list HTTP', r.status, 'ids', len(d.get('data', [])), round(time.time() - t, 2), 's')
ids = [m.get('id') for m in d.get('data', [])]
print('argon listed', 'gcp/google/gemini-4-argon' in ids, 'astra listed', 'openai/openai/gpt-6.2-astra' in ids)
PY
fi
cd $J && NVO=$J NVO_TARS=/project/community/jjyeung/okh7/e6fc152498/a2.tar NVO_WORKERS=${NVO_WORKERS:-48} python3 -B $J/kit/nvo_run.py "${1:-600}"
echo "runner rc $? end $(date -u +%FT%TZ)"
