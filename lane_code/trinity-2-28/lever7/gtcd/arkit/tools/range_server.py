"""Local test server: python's http.server (SimpleHTTPRequestHandler) plus single-range GETs (206, suffix ranges) and fault
injection, for rehearsing fetch_arkit.py without the network. Binds 127.0.0.1 only.
usage: range_server.py ROOT PORT [FAULTS.json]   FAULTS: [{"match": "<substring of 'path range'>", "mode": "500"|"200", "times": n}]"""
import http.server, json, os, re, sys

ROOT, PORT = sys.argv[1], int(sys.argv[2])
FAULTS = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else []
LOG = open(os.path.join(os.path.dirname(os.path.abspath(ROOT)), 'server_%d.log' % PORT), 'a', buffering=1)


class H(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, fmt, *args):
        LOG.write('%s %s\n' % (self.log_date_time_string(), fmt % args))

    def do_GET(self):
        path = self.translate_path(self.path)
        rng = self.headers.get('Range', '')
        LOG.write('GET %s %s UA=%s\n' % (self.path, rng, self.headers.get('User-Agent')))
        for f in FAULTS:
            if f['times'] > 0 and f['match'] in '%s %s' % (self.path, rng):
                f['times'] -= 1
                if f['mode'] == '500':
                    body = b'injected fault'
                    self.send_response(500); self.send_header('Content-Length', str(len(body))); self.end_headers()
                    self.wfile.write(body); return
                rng = ''   # mode 200: ignore the range and send the whole file
        if not os.path.isfile(path):
            self.send_error(404); return
        size = os.path.getsize(path)
        m = re.match(r'bytes=(\d*)-(\d*)$', rng)
        with open(path, 'rb') as fh:
            if not m:
                self.send_response(200); self.send_header('Content-Length', str(size)); self.end_headers()
                self.wfile.write(fh.read()); return
            a, b = m.groups()
            if a == '':
                lo, hi = max(0, size - int(b)), size - 1
            else:
                lo, hi = int(a), min(int(b) if b else size - 1, size - 1)
            fh.seek(lo); data = fh.read(hi - lo + 1)
        self.send_response(206)
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (lo, hi, size))
        self.send_header('Content-Length', str(len(data))); self.end_headers()
        self.wfile.write(data)


http.server.ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
