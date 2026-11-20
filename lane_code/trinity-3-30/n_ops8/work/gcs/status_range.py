"""n_ops8: zero-length status PUT on named sessions; prints HTTP code, Range and size headers only (never the URI)."""
import json,sys,urllib.request,urllib.error
s=json.load(open(sys.argv[1]))
for n in sys.argv[2:]:
  req=urllib.request.Request(s[n],data=b'',method='PUT',headers={'Content-Range':'bytes */*','Content-Length':'0'})
  try:
    with urllib.request.urlopen(req,timeout=60) as r:c=r.status;h=r.headers
  except urllib.error.HTTPError as e:c=e.code;h=e.headers
  body={}
  if c in (200,201):
    try:body={k:v for k,v in json.loads(r.read() if False else b'{}').items()}
    except Exception:pass
  print(json.dumps(dict(name=n,http_status=c,range=h.get('Range'),x_guploader_status=h.get('X-Goog-Upload-Status'),content_length=h.get('Content-Length'))))
