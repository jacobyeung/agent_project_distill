set +x
echo "host $(hostname) $(date -u +%FT%TZ)"
printf 'header = "Authorization: Bearer %s"\nheader = "Content-Type: application/json"\nheader = "dataClassification: sensitive"\n' "$NVK_A" | curl -s -m 60 -K - -D /dev/stderr -w '\nHTTP %{http_code} %{time_total}\n' -d '{"model": "gcp/google/gemini-3.8-flash", "messages": [{"role": "user", "content": "Reply with the single word OK."}], "max_tokens": 16, "reasoning_effort": "low"}' https://inference-api.nvidia.com/v1/chat/completions 2>/tmp/nvk1_hdr_$$ | python3 -c "
import sys, json
t = sys.stdin.read(); body, _, tail = t.rpartition('\nHTTP ')
print('chat HTTP', tail.strip())
try:
    d = json.loads(body); print('served', d.get('model'), 'usage', d.get('usage'), 'text', repr(((d.get('choices') or [{}])[0].get('message') or {}).get('content')))
except Exception as e: print('body', body[:300])
"
grep -i -E '^(x-litellm-response-cost|x-amzn|x-litellm-model|retry-after|x-ratelimit)' /tmp/nvk1_hdr_$$ | cut -c1-120
: > /tmp/nvk1_hdr_$$
unset NVK_A
