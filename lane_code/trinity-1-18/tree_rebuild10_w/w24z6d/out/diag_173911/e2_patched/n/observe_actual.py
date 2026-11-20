"""Retain capability-free child and HTTP diagnostics outside the sealed kit."""
import sys, os, json, runpy, subprocess, http.client, time, hashlib, re, ssl
from pathlib import Path
N = Path(os.environ["E2_N"]); K = N / "k"
ERRORS = {"OSError", "IOError", "TimeoutError", "ConnectionError", "ConnectionResetError",
          "BrokenPipeError", "PermissionError", "FileNotFoundError", "ValueError", "TypeError",
          "KeyError", "AttributeError", "JSONDecodeError", "SSLError", "SSLCertVerificationError",
          "gaierror", "RemoteDisconnected", "IncompleteRead", "BadStatusLine", "PicklingError",
          "BrokenProcessPool", "RuntimeError", "ImportError", "ModuleNotFoundError"}

def error_fields(error):
    name = type(error).__name__
    return dict(error=name if name in ERRORS else "OtherError",
                errno=getattr(error, "errno", None) if isinstance(getattr(error, "errno", None), int) else None)

def event(kind, **fields):
    # Only caller-selected numeric fields, enums and hashes enter this channel.
    row = dict(event=kind, pid=os.getpid(), time_ns=time.time_ns(), **fields)
    raw = (json.dumps(row, sort_keys=True) + "\n").encode()
    try:
        fd = os.open(N / "logs/upload.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try: os.write(fd, raw)
        finally: os.close(fd)
    except OSError:
        # An unavailable local diagnostic disk is reported without exception text.
        os.write(2, b"E2_DIAGNOSTIC_WRITE_FAILED\n")

args = sys.argv[1:]
while args and args[0].startswith("-"): args.pop(0)
script = Path(args[0]).resolve(); sys.argv = args
if script not in {(K / "b" / name).resolve() for name in ("pc.py", "gc.py", "o.py", "ep.py", "sr.py")}:
    raise SystemExit(92)
sys.path.insert(0, str(K / "b"))
if script.name == "pc.py":
    original = subprocess.run
    def run(argv, *a, **kw):
        child = None
        if isinstance(argv, list) and any(str(K / "b" / name) in argv for name in ("gc.py", "o.py")):
            i = next(i for i, v in enumerate(argv) if v in (str(K / "b/gc.py"), str(K / "b/o.py")))
            child = Path(argv[i]).name
            event("child_start", child=child)
            argv = argv[:i] + [str(N / "observe.py")] + argv[i:]
        try:
            result = original(argv, *a, **kw)
        except Exception as error:
            if child: event("child_exception", child=child, **error_fields(error))
            raise
        if child: event("child_exit", child=child, returncode=result.returncode)
        return result
    subprocess.run = run
if script.name == "gc.py":
    import multiprocessing
    event("writer_runtime", object_tag=hashlib.sha256(args[3].encode()).hexdigest(), python=list(sys.version_info[:3]),
          start_method=multiprocessing.get_start_method(),
          openssl=ssl.OPENSSL_VERSION_NUMBER,
          ca_file_override=bool(os.environ.get("SSL_CERT_FILE")),
          ca_dir_override=bool(os.environ.get("SSL_CERT_DIR")))
    class SafeStderr:
        """Keep classified stderr evidence; never persist exception/body text."""
        def write(self, text):
            classes = sorted(name for name in ERRORS if re.search(r"\b" + re.escape(name) + r"\b", text))
            statuses = [int(v) for v in re.findall(r"\bHTTP ([1-5][0-9]{2})\b", text)]
            if text.strip(): event("gc_stderr", errors=classes, http_statuses=statuses)
            return len(text)
        def flush(self): pass
    sys.stderr = SafeStderr()
    Original = http.client.HTTPSConnection
    class Reply:
        def __init__(self, reply): self.r = reply; self.status = reply.status
        def read(self, *a, **kw):
            try: raw = self.r.read(*a, **kw)
            except Exception as error:
                event("http_read_error", **error_fields(error)); raise
            if self.status in (200, 201):
                try:
                    v = json.loads(raw)
                    keep = {key: v.get(key) for key in ("size", "crc32c", "md5Hash", "name", "generation")}
                    # Response metadata is saved separately; the session URI never is.
                    p = N / "obs" / ("r_" + str(os.getpid()) + "_" + str(time.time_ns()) + ".json")
                    p.write_text(json.dumps(keep, sort_keys=True) + "\n")
                except (ValueError, OSError) as error:
                    event("metadata_capture_error", **error_fields(error))
            return raw
        def __getattr__(self, name): return getattr(self.r, name)
    class Connection(Original):
        def putrequest(self, method, url, *a, **kw):
            self.request_id = time.time_ns()
            event("http_request", request_id=self.request_id, method="PUT" if method == "PUT" else "OTHER")
            return super().putrequest(method, url, *a, **kw)
        def connect(self):
            try: return super().connect()
            except Exception as error:
                event("connect_error", request_id=self.request_id, **error_fields(error)); raise
        def getresponse(self):
            try: reply = super().getresponse()
            except Exception as error:
                event("http_response_error", request_id=self.request_id, **error_fields(error)); raise
            value = reply.getheader("Range")
            event("http_status", request_id=self.request_id, status=reply.status,
                  range=value if value and re.fullmatch(r"bytes=0-[0-9]+", value) else None)
            return Reply(reply)
    http.client.HTTPSConnection = Connection
try:
    runpy.run_path(str(script), run_name="__main__")
except SystemExit as error:
    if isinstance(error.code, str):
        event("child_system_exit_message", child=script.name)
        print("E2_CHILD_FAIL", file=sys.stderr); raise SystemExit(1)
    raise
except Exception as error:
    event("child_error", child=script.name, **error_fields(error))
    print("E2_CHILD_FAIL " + error_fields(error)["error"], file=sys.stderr); raise SystemExit(1)
