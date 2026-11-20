import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
N = {'n': 0}
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        N['n'] += 1; m = body['model']
        assert self.headers.get('dataClassification') == 'sensitive'
        assert self.headers.get('Authorization', '').startswith('Bearer ')
        served = {'gcp/google/gemini-4-argon': 'gemini-4-argon', 'openai/openai/gpt-6.2-astra': 'gpt-6.2-astra-2026-10-01', 'azure/anthropic/claude-opus-5-5': 'claude-opus-4-8'}.get(m, m)
        if N['n'] == 2:
            self.send_response(503); self.end_headers(); self.wfile.write(b'{"error": "busy"}'); return
        nimg = sum(1 for c in body['messages'][0]['content'] if c['type'] == 'image_url')
        out = {'model': served, 'choices': [{'message': {'content': '{"ok": %d}' % nimg}, 'finish_reason': 'stop'}],
               'usage': {'prompt_tokens': 1000 * nimg + 50, 'completion_tokens': 300, 'completion_tokens_details': {'reasoning_tokens': 200}}}
        b = json.dumps(out).encode(); self.send_response(200); self.send_header('x-litellm-response-cost', '0.0123'); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
HTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
