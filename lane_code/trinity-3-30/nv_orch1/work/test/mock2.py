import json, sys, http.server
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        txt = b['messages'][0]['content'][0]['text']
        if 'Another annotator' in txt: c = json.dumps({'frames': {'1': {'chair': [1, 2]}}, 'rejects': [], 'missed': [], 'saw': txt[:120]})
        else: c = '```json\n' + json.dumps({'objects': [{'name': 'chair', 'aliases': ['seat', 'stool'], 'lookalike': 'bench', 'count': 2, 'frames': [1], 'points': {'1': [5, 5]}}], 'nouns': {'a': 'absent'}}) + '\n```'
        out = json.dumps({'model': b['model'], 'choices': [{'message': {'content': c}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1000, 'completion_tokens': 100}}).encode()
        self.send_response(200); self.send_header('x-litellm-response-cost', '0.001'); self.end_headers(); self.wfile.write(out)
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
