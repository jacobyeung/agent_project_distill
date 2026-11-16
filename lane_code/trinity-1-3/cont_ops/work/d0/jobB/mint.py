"""Mint resumable GCS upload sessions for b/gcsput.py (stdlib + the gcloud CLI on this node).
For each export milestone M of RUN: object names q8/<KIT_ID>/<RUN>_<M>.tar.partNN-of-04 (NN = 00..03), the names
c.sh tk_persist_exports and gcsput.py look up. Each session is created with ifGenerationMatch=0, so it can only create a
new object, never replace one. The access token comes from `gcloud auth print-access-token` and is never printed or
written; the session URIs go only into OUT (created with mode 600, refused if it exists). Prints names and counts only.
Usage: mint.py OUT KIT_ID RUN M [M ...]
       mint.py --status OUT NAME   (zero-length status query of one session: prints the HTTP status only)"""
import json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request

BUCKET = 'cmu-gpucloud-jjyeung'


def token():
    return subprocess.run(['gcloud', 'auth', 'print-access-token'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          check=True, timeout=120).stdout.decode().strip()


def mint(out, kit, run, milestones):
    if not re.fullmatch('[0-9a-f]{8}', kit) or not re.fullmatch('[0-9a-f]{8}', run): raise SystemExit('ids must be 8 hex digits')
    if not milestones or not all(re.fullmatch(r'm(\d+|stop[BC]?)', m) for m in milestones): raise SystemExit('milestones: m<N>, mstop, mstopB, mstopC')
    names = [f'q8/{kit}/{run}_{m}.tar.part{i:02d}-of-04' for m in milestones for i in range(4)]
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    auth, sessions = token(), {}
    for n in names:
        q = urllib.parse.urlencode(dict(uploadType='resumable', name=n, ifGenerationMatch='0'))
        req = urllib.request.Request(f'https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o?{q}', data=b'{}', method='POST',
                                     headers={'Authorization': 'Bearer ' + auth, 'Content-Type': 'application/json; charset=UTF-8',
                                              'X-Upload-Content-Type': 'application/octet-stream'})
        with urllib.request.urlopen(req, timeout=60) as r:
            loc = r.headers.get('Location')
            if r.status != 200 or not loc or not loc.startswith('https://storage.googleapis.com/upload/'): raise SystemExit('mint failed for ' + n)
        sessions[n] = loc
    with os.fdopen(fd, 'w') as f:
        json.dump(sessions, f, sort_keys=True, indent=1); f.write('\n')
    print(json.dumps(dict(minted=len(sessions), first=names[0], last=names[-1])))


def status(out, name):
    uri = json.load(open(out))[name]
    req = urllib.request.Request(uri, data=b'', method='PUT', headers={'Content-Range': 'bytes */*', 'Content-Length': '0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: code = r.status
    except urllib.error.HTTPError as e: code = e.code
    print(json.dumps(dict(name=name, http_status=code)))


if __name__ == '__main__':
    if sys.argv[1] == '--status': status(sys.argv[2], sys.argv[3])
    else: mint(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
