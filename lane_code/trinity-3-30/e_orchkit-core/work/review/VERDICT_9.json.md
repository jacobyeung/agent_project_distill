{
  "schema": "orchkit-verdict-v1",
  "reviewer_lane": "codex_review_orchkit_core_9",
  "requested_head": "3c731cbc",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "validation": {
    "method": "Reran OC-01..OC-24 and OC-26 using the permitted earlier reproductions, with filesystem mocks adapted to current snapshots, locks, token claims and payload identities. Preparation, pin verification, scanning, rebuilding and submission validation ran against in-memory files. Transport was mocked.",
    "status_scope": "Fixed means the original reproduction now satisfies the specification. Related remaining cases are reported separately below.",
    "unit_test_output": "Ran 1 test in 0.002s\nOK",
    "full_suite": "Not run because filesystem writes are unavailable in this read-only session.",
    "controls": [
      "NO_GO and GO naming another token: refused, zero transport calls.",
      "GO naming the correct job: accepted, one mocked transport call.",
      "Remote live gate: empty queue accepted; existing job refused; correctly named QUEUE_BEHIND accepted; wrong QUEUE_BEHIND refused.",
      "Room checks: full home allocation attempted; home quota shortage refused; pool quota shortage refused after successful home check."
    ],
    "side_effects": "No files changed. No Git, SSH, Slurm or network commands ran. Scheduler-query checks used a local shell function. No jobs were submitted."
  },
  "findings": [
    {
      "id": "OC-01",
      "text": {
        "status": "fixed",
        "detail": "All five original fixtures are detected or refused."
      },
      "output": "disguised_gzip: rule 19; depth_five: too-deep; tar_uname: rule 19; fifo_bytes: rule 19 and special; utf16: rule 19"
    },
    {
      "id": "OC-02",
      "text": {
        "status": "fixed",
        "detail": "Preparation refuses each original root, environment and pool fixture."
      },
      "output": "root, env, pool: REFUSED CONFIG.json opacity rule 7"
    },
    {
      "id": "OC-03",
      "text": {
        "status": "fixed",
        "detail": "Both original naming bypasses are detected."
      },
      "output": "ORCH_N30: rule 29; orchkit-pins-v1-private: rule 39"
    },
    {
      "id": "OC-04",
      "text": {
        "status": "fixed",
        "detail": "The trailing-newline token is refused. The job-name unit test also passes."
      },
      "output": "REFUSED token must be 16 lowercase hex: '0123456789abcdef\\n'"
    },
    {
      "id": "OC-05",
      "text": {
        "status": "fixed",
        "detail": "A failed scheduler query stops the remote gate."
      },
      "output": "rc=6 stdout=LIVE unknown: squeue failed"
    },
    {
      "id": "OC-06",
      "text": {
        "status": "fixed",
        "detail": "The room check attempts the full allocation and refuses the simulated quota shortage."
      },
      "output": "SHORT home [Errno 122] Disk quota exceeded; exit 3; allocated [104857600]"
    },
    {
      "id": "OC-07",
      "text": {
        "status": "fixed",
        "detail": "Interleaving another submission immediately before intent creation permits only one transport call. A nested attempt during transport is also refused."
      },
      "output": "second at intent: REFUSED another submission to this partition is in progress; first: SUBMITTED; calls 1"
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "Changing SUBMIT.sh after loading causes refusal. Changing it at intent creation cannot replace the rebuilt bytes sent."
      },
      "output": "after_load: calls 0; at_intent: calls 1; altered_sent False"
    },
    {
      "id": "OC-09",
      "text": {
        "status": "fixed",
        "detail": "The original forbidden gzip filename and bz2/xz trailers are detected. OC-28 covers a remaining name-only rule gap."
      },
      "output": "gzip_filename: rule 19; bz2_trailer and xz_trailer: rule 19 and undecodable"
    },
    {
      "id": "OC-10",
      "text": {
        "status": "fixed",
        "detail": "The compression-header copy of a pinned hash violates the single-place check."
      },
      "output": "a.bin: copy of a pinned hash outside PINS.json"
    },
    {
      "id": "OC-11",
      "text": {
        "status": "fixed",
        "detail": "Changing the source kit during provenance leaves the checked snapshot unchanged."
      },
      "output": "SUBMITTED calls 1 shipped b'ok'"
    },
    {
      "id": "OC-12",
      "text": {
        "status": "fixed",
        "detail": "The original token-only metadata substitution is refused."
      },
      "output": "REFUSED the prepared scripts do not belong to token fedcba9876543210; transport_calls 0"
    },
    {
      "id": "OC-13",
      "text": {
        "status": "fixed",
        "detail": "Ordinary and prefixed ZIP fixtures are inspected and refused."
      },
      "output": "Both fixtures: a.zip!/x rule 19; prepare REFUSED opacity"
    },
    {
      "id": "OC-14",
      "text": {
        "status": "fixed",
        "detail": "Duplicate-key values, root strings and UTF-16 copies of pinned hashes are detected."
      },
      "output": "duplicate_key, root_string, utf16: prepare REFUSED single-place invariant"
    },
    {
      "id": "OC-15",
      "text": {
        "status": "fixed",
        "detail": "Appending an empty ZIP no longer hides the tar interpretation."
      },
      "output": "opacity fixture: REFUSED rule 19 at a.bin!/x.gz!gz; hash fixture: REFUSED single-place invariant"
    },
    {
      "id": "OC-16",
      "text": {
        "status": "fixed",
        "detail": "Both original command substitutions are refused before transport."
      },
      "output": "script: SUBMIT.sh differs from its rebuild; argv: transport command differs; transport_calls 0"
    },
    {
      "id": "OC-17",
      "text": {
        "status": "fixed",
        "detail": "The forbidden path in the discarded duplicate CONFIG.json value is detected."
      },
      "output": "REFUSED CONFIG.json opacity rule 7"
    },
    {
      "id": "OC-18",
      "text": {
        "status": "fixed",
        "detail": "All four original Unicode-escape representations are detected."
      },
      "output": "utf16, utf32, gzip_json, json_without_extension: rule 19; prepare REFUSED opacity"
    },
    {
      "id": "OC-19",
      "text": {
        "status": "fixed",
        "detail": "The original damaged ZIP is refused."
      },
      "output": "a.zip: unsupported-container; prepare REFUSED unscannable"
    },
    {
      "id": "OC-20",
      "text": {
        "status": "fixed",
        "detail": "Changing PREP/kit/data.bin at the JOB.json read is caught by submission-snapshot validation."
      },
      "output": "REFUSED pins differ: actual bytes 4, expected bytes 2; calls 0"
    },
    {
      "id": "OC-21",
      "text": {
        "status": "fixed",
        "detail": "Two preparation copies reach transport only once. A separate check confirms that the shared token claim refuses a second claim."
      },
      "output": "transport_calls 1; submitted_rows 1; second shared claim REFUSED token 0123456789abcdef was already claimed"
    },
    {
      "id": "OC-22",
      "text": {
        "status": "fixed",
        "detail": "Mutating partition metadata now causes refusal. The unchanged concurrent-submission control permits one transport call."
      },
      "output": "control: calls 1, outcomes ['REFUSED', 'SUBMITTED']; mutation: REFUSED partition differs between config, ledger and SUBMIT.json"
    },
    {
      "id": "OC-23",
      "text": {
        "status": "fixed",
        "detail": "The original octal, named-character and JSON slash escapes are detected. OC-27 covers another standard Python escape."
      },
      "output": "octal and named: REFUSED rule 19; escaped slash: REFUSED rule 24"
    },
    {
      "id": "OC-24",
      "text": {
        "status": "fixed",
        "detail": "Both original damaged-container fixtures are refused. OC-29 covers the remaining tar recognition gap with a UTF-8 filename."
      },
      "output": "prefixed ZIP and bad-checksum tar: unsupported-container; prepare REFUSED unscannable"
    },
    {
      "id": "OC-25",
      "text": {
        "status": "resolved_by_specification",
        "detail": "Ordinary file contents may contain split. The earlier finding is withdrawn under the clarified name-only rule."
      }
    },
    {
      "id": "OC-26",
      "text": {
        "status": "fixed",
        "detail": "Changing JOB.json sessions or adding an unminted DRYRUN_REPORT.json fails the whole-bundle payload comparison."
      },
      "output": "JOB and DRYRUN: REFUSED payload differs from the one its ledger row names; transport_calls 0"
    },
    {
      "id": "OC-27",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 85,
      "line_end": 120,
      "text": {
        "status": "not fixed",
        "detail": "A standard Python backslash-newline escape hides qwen. Python removes the escaped newline, but _unescape leaves it intact. Preparation accepts and preserves the file."
      },
      "repro_python": "blob=b'x = \"q'+bytes([92,10])+b'wen\"\\n'\nconfirm('line_continuation','a.py',blob,ast.literal_eval(blob.decode().partition('=')[2].strip()))",
      "output": "line_continuation hits [] prepare ACCEPTED unchanged True decoded 'qwen'",
      "expect": "Detect the forbidden word after standard Python line-continuation decoding, or refuse the representation."
    },
    {
      "id": "OC-28",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 223,
      "line_end": 253,
      "text": {
        "status": "not fixed",
        "detail": "The gzip original-filename header receives only text checks. A normal gzip stream whose stored filename is split.txt passes preparation. This is a filename violation, separate from the permitted use of split in ordinary contents."
      },
      "repro_python": "raw=io.BytesIO()\nwith gzip.GzipFile(filename='split.txt',fileobj=raw,mode='wb',mtime=0) as a:a.write(b'ok')\nconfirm('gzip_fname','a.gz',raw.getvalue(),raw.getvalue()[10:].split(bytes([0]),1)[0])",
      "output": "gzip_fname hits [] prepare ACCEPTED unchanged True decoded b'split.txt'",
      "expect": "Apply name rules to the gzip original-filename field."
    },
    {
      "id": "OC-29",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 143,
      "line_end": 180,
      "text": {
        "status": "not fixed",
        "detail": "Damaged V7-style tar recognition requires an ASCII filename. A UTF-8 filename makes the same invalid-checksum container fall through as an ordinary file. Python refuses the tar, but preparation accepts it unchanged."
      },
      "repro_python": "raw=io.BytesIO()\nwith tarfile.open(fileobj=raw,mode='w',format=tarfile.USTAR_FORMAT) as a:\n blob=gzip.compress(b'qwen');m=tarfile.TarInfo('caf\\u00e9.gz');m.size=len(blob);a.addfile(m,io.BytesIO(blob))\nbad=bytearray(raw.getvalue());bad[257:265]=bytes(8);bad[148:156]=b'0000000'+bytes(1)\ntry:tarfile.open(fileobj=io.BytesIO(bad),mode='r:')\nexcept tarfile.ReadError as e:print('bad_unicode_tar Python',type(e).__name__,str(e))\nconfirm('bad_unicode_tar','a.tar',bytes(bad),'Python refuses')",
      "output": [
        "bad_unicode_tar Python ReadError bad checksum",
        "bad_unicode_tar hits [] prepare ACCEPTED unchanged True decoded 'Python refuses'"
      ],
      "expect": "Refuse the damaged container regardless of whether its filename is ASCII or UTF-8."
    },
    {
      "id": "OC-30",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 132,
      "line_end": 165,
      "text": {
        "status": "not fixed",
        "detail": "The standard LZMA-alone container is neither inspected nor refused. Python creates and decompresses this format directly; a stream containing qwen passes preparation unchanged."
      },
      "repro_python": "import lzma\nblob=lzma.compress(b'qwen',format=lzma.FORMAT_ALONE)\nconfirm('lzma_alone','a.lzma',blob,lzma.decompress(blob))",
      "output": "lzma_alone hits [] prepare ACCEPTED unchanged True decoded b'qwen'",
      "expect": "Inspect this standard container or refuse it."
    },
    {
      "id": "OC-31",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/ANON_WORDS.txt",
      "line_start": 24,
      "line_end": 24,
      "text": {
        "status": "not fixed",
        "detail": "The cluster-path rule misses a bare mount root and a path with a redundant leading slash. Both /data2 and //data2/secret are accepted as job.root_parent, while /data2/secret is refused. The accepted paths enter the configuration and rendered batch script."
      },
      "repro_python": "for path in ['/data2','//data2/secret']:\n files,c=fixture(change=lambda c:c['job'].update(root_parent=path))\n with environment(files):\n  print('path',repr(path),'schema',launch.validate_config(c),'name_hits',anon.scan_text('path',path,rules,'name'))\n  print('prepare',path,'ACCEPTED',prep(files)['token'])",
      "output": [
        "path '/data2' schema [] name_hits []",
        "prepare /data2 ACCEPTED 0123456789abcdef",
        "path '//data2/secret' schema [] name_hits []",
        "prepare //data2/secret ACCEPTED 0123456789abcdef"
      ],
      "expect": "Reject cluster mount roots and their ordinary absolute-path variants."
    }
  ],
  "reproduction_context": {
    "instructions": "Run python_prelude followed by one new finding's repro_python in a fresh /usr/bin/python3 -B -c process. The permitted earlier verdict supplies in-memory fixtures and filesystem mocks.",
    "environment": {
      "TMPDIR": "/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONPATH": "/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools"
    },
    "python_prelude": "import json\np='/scratch/jjyeung/orch_n30/e_orchkit-core/work/review/VERDICT_8.json.md'\nwith open(p) as f:v=json.JSONDecoder().raw_decode(f.read())[0]\nexec(v['reproduction_context']['python_prelude'])\ndef confirm(label,name,blob,decoded):\n files,c=fixture({name:blob})\n with environment(files):\n  hits=anon.scan_tree('/v/kit',rules)\n  prep(files)\n  print(label,'hits',hits,'prepare ACCEPTED','unchanged',payload(files)['kit/'+name]==blob,'decoded',repr(decoded))"
  }
}

All 25 requested reproductions now pass. OC-25 is resolved by clarification.
Five additional naming or container bypasses keep the verdict at NO_GO.
No files changed or jobs were submitted.