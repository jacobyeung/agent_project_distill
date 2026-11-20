set +x
W=/scratch/jjyeung/orch_n30/nvkey1; mkdir -p $W/work $W/out $W/inbox
echo "== host $(hostname -s) $(date -u +%FT%TZ)"; df -h /scratch | tail -1; nproc; uptime; free -g | head -2
echo "== tmux"; tmux ls 2>&1 | head -20
echo "== scratch/jjyeung"; ls /scratch/jjyeung/ | head -40
echo "== orch_n30"; ls /scratch/jjyeung/orch_n30/ | head -60
echo "== k1_frames"; ls /scratch/jjyeung/k1_frames | head -5; ls /scratch/jjyeung/k1_frames | wc -l
f=$(ls /scratch/jjyeung/k1_frames | head -1); [ -n "$f" ] && { ls -la /scratch/jjyeung/k1_frames/$f | head -8; ls /scratch/jjyeung/k1_frames/$f | wc -l; }
echo "== point"; ls -la /scratch/jjyeung/orch_n30/fb_pack/point/out 2>&1 | head -20
echo "== ro"; ls /scratch/jjyeung/orch_n30/fb_pack/ro 2>&1 | head; ls /scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30 2>&1 | head -40
echo "== envs"; ls /scratch/jjyeung/envs 2>&1
p=/scratch/jjyeung/envs/p1cpu/bin/python; $p -c "import sys;print(sys.version.split()[0])" 2>&1; $p -c "import PIL, numpy; print('PIL', PIL.__version__, 'np', numpy.__version__)" 2>&1 | tail -1; $p -c "import openai; print('openai', openai.__version__)" 2>&1 | tail -1; $p -c "import requests; print('requests', requests.__version__)" 2>&1 | tail -1
echo "== catalogue"
v=NV_INFERENCE_API_KEY; [ -n "${!v:-}" ] || eval "$(grep -m1 "^export $v=" ~/.bashrc)"
if [ -z "${!v:-}" ]; then echo "key unset"; else
  for ep in v1/models model/info v1/model/info; do
    o=$W/work/cat_$(echo $ep | tr '/' '_').json
    c=$(printf 'header = "Authorization: Bearer %s"\n' "${!v}" | curl -s -m 60 -K - -o $o -w '%{http_code} %{size_download}' https://inference-api.nvidia.com/$ep)
    echo "$ep -> $c"
  done
  printf 'header = "Authorization: Bearer %s"\n' "${!v}" | curl -s -m 60 -K - https://inference-api.nvidia.com/key/info | $p -c "
import sys, json
try:
    d=json.load(sys.stdin); info=d.get('info', d) if isinstance(d, dict) else {}
    print('key_info', {k: info.get(k) for k in ('spend','max_budget','budget_duration','budget_reset_at','tpm_limit','rpm_limit','max_parallel_requests')})
except Exception as e: print('key_info parse', type(e).__name__)
"
fi
unset NV_INFERENCE_API_KEY
$p - <<'PY'
import json
W='/scratch/jjyeung/orch_n30/nvkey1/work/'
try:
    d=json.load(open(W+'cat_v1_models.json')); ids=sorted(m['id'] for m in d.get('data',[]))
    print('n ids', len(ids)); print(' '.join(ids))
except Exception as e: print('models parse', e)
for fn in ('cat_model_info.json', 'cat_v1_model_info.json'):
    try:
        d=json.load(open(W+fn)); rows=d.get('data',[])
        print(fn, 'rows', len(rows))
        out=[]
        for r in rows:
            mi=r.get('model_info') or {}
            out.append(dict(name=r.get('model_name'), inp=mi.get('input_cost_per_token'), outp=mi.get('output_cost_per_token'), vision=mi.get('supports_vision'), reason=mi.get('supports_reasoning'), mi=mi.get('max_input_tokens'), mo=mi.get('max_output_tokens'), prov=mi.get('litellm_provider')))
        json.dump(out, open(W+'costs_'+fn,'w'), indent=0)
        for o in out:
            if o['vision']: print('V', o['name'], o['inp'], o['outp'], o['reason'], o['mi'], o['mo'], o['prov'])
        break
    except Exception as e: print(fn, 'parse', e)
PY
echo "== done"
