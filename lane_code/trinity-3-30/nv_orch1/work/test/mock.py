import json, sys, http.server, threading
N = {'n': 0}
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers['Content-Length']))); N['n'] += 1
        nimg = sum(1 for c in b['messages'][0]['content'] if c['type'] == 'image_url')
        if N['n'] == int(sys.argv[2]):
            self.send_response(429); self.send_header('x-amzn-waf-action', 'block'); self.end_headers(); self.wfile.write(b'{}'); return
        out = json.dumps({'model': b['model'], 'choices': [{'message': {'content': '{"images": %d}' % nimg}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1000, 'completion_tokens': 100}}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('x-litellm-response-cost', '0.001'); self.end_headers(); self.wfile.write(out)
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
