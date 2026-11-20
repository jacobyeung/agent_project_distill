set +x
echo "host $(hostname) $(date -u +%FT%TZ)"
command -v curl >/dev/null || { echo "no curl"; exit 0; }
printf 'header = "Authorization: Bearer %s"\n' "$NVK_A" | curl -s -m 30 -K - -w '\nHTTP %{http_code} %{size_download} %{time_total}\n' https://inference-api.nvidia.com/v1/models 2>&1 | python3 -c "
import sys, json
t = sys.stdin.read(); body, _, tail = t.rpartition('\nHTTP ')
print('models-list HTTP', tail.strip())
try: print('ids', len(json.loads(body).get('data', [])))
except Exception as e: print('body not json', type(e).__name__, len(body))
"
unset NVK_A
